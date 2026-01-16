from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta
from io import BytesIO, StringIO
import csv

from app.database import get_db
from app.models.collection import Collection, collection_channels
from app.models.collection_share import CollectionShare
from app.models.channel import Channel
from app.models.message import Message
from app.models.summary import Summary
from app.models.user import User
from app.schemas.collection import CollectionCreate, CollectionResponse, CollectionUpdate, CollectionStatsResponse
from app.schemas.collection_share import CollectionShareCreate, CollectionShareResponse
from app.schemas.summary import SummaryResponse, SummaryListResponse
from app.auth.users import current_active_user
from app.services.audit import record_audit_event
from app.services.summarizer import generate_daily_summary

router = APIRouter()


async def _load_channels(db: AsyncSession, channel_ids: List[UUID]) -> List[Channel]:
    if not channel_ids:
        return []
    result = await db.execute(select(Channel).where(Channel.id.in_(channel_ids)))
    channels = result.scalars().all()
    if len(channels) != len(set(channel_ids)):
        raise HTTPException(status_code=400, detail="One or more channels not found")
    return channels


async def _load_all_channels(db: AsyncSession) -> List[Channel]:
    result = await db.execute(select(Channel).where(Channel.is_active == True))
    return result.scalars().all()


async def _apply_default_collection(db: AsyncSession, user_id: UUID, collection: Collection):
    if collection.is_default:
        await db.execute(
            update(Collection)
            .where(Collection.user_id == user_id, Collection.id != collection.id)
            .values(is_default=False)
        )


async def _collection_channel_ids(db: AsyncSession, collection: Collection) -> List[UUID]:
    if collection.is_global:
        channels = await _load_all_channels(db)
        return [channel.id for channel in channels]
    return [channel.id for channel in collection.channels]


def _collection_response(collection: Collection, channel_ids: List[UUID]) -> CollectionResponse:
    return CollectionResponse(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        description=collection.description,
        color=collection.color,
        icon=collection.icon,
        is_default=collection.is_default,
        is_global=collection.is_global,
        parent_id=collection.parent_id,
        auto_assign_languages=collection.auto_assign_languages or [],
        auto_assign_keywords=collection.auto_assign_keywords or [],
        auto_assign_tags=collection.auto_assign_tags or [],
        channel_ids=channel_ids,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


async def _get_collection_for_user(
    db: AsyncSession,
    collection_id: UUID,
    user_id: UUID,
) -> tuple[Collection, Optional[str]]:
    result = await db.execute(
        select(Collection, CollectionShare.permission)
        .outerjoin(
            CollectionShare,
            (CollectionShare.collection_id == Collection.id) & (CollectionShare.user_id == user_id),
        )
        .where(Collection.id == collection_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Collection not found")
    collection, permission = row
    if collection.user_id != user_id and not permission:
        raise HTTPException(status_code=403, detail="Not authorized to access this collection")
    return collection, permission


@router.get("", response_model=List[CollectionResponse])
async def list_collections(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.channels))
        .outerjoin(
            CollectionShare,
            (CollectionShare.collection_id == Collection.id) & (CollectionShare.user_id == user.id),
        )
        .where(or_(Collection.user_id == user.id, CollectionShare.user_id == user.id))
    )
    collections = result.scalars().all()
    responses = []
    for collection in collections:
        channel_ids = await _collection_channel_ids(db, collection)
        responses.append(_collection_response(collection, channel_ids))
    return responses


@router.get("/overview")
async def get_collections_overview(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.channels))
        .outerjoin(
            CollectionShare,
            (CollectionShare.collection_id == Collection.id) & (CollectionShare.user_id == user.id),
        )
        .where(or_(Collection.user_id == user.id, CollectionShare.user_id == user.id))
    )
    collections = result.scalars().all()
    overview = []
    week_ago = datetime.utcnow() - timedelta(days=7)
    for collection in collections:
        channel_ids = await _collection_channel_ids(db, collection)
        if not channel_ids:
            overview.append(
                {
                    "id": str(collection.id),
                    "name": collection.name,
                    "message_count_7d": 0,
                    "channel_count": 0,
                    "created_at": collection.created_at,
                }
            )
            continue
        count_result = await db.execute(
            select(func.count())
            .select_from(Message)
            .where(Message.channel_id.in_(channel_ids))
            .where(Message.published_at >= week_ago)
        )
        overview.append(
            {
                "id": str(collection.id),
                "name": collection.name,
                "message_count_7d": count_result.scalar() or 0,
                "channel_count": len(channel_ids),
                "created_at": collection.created_at,
            }
        )
    return {"collections": overview}


@router.post("", response_model=CollectionResponse)
async def create_collection(
    payload: CollectionCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    channels = await _load_channels(db, payload.channel_ids or [])
    if payload.is_global:
        channels = []
    if payload.parent_id:
        await _get_collection_for_user(db, payload.parent_id, user.id)

    collection = Collection(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        color=payload.color,
        icon=payload.icon,
        is_default=payload.is_default,
        is_global=payload.is_global,
        parent_id=payload.parent_id,
        auto_assign_languages=payload.auto_assign_languages or [],
        auto_assign_keywords=payload.auto_assign_keywords or [],
        auto_assign_tags=payload.auto_assign_tags or [],
        channels=channels,
    )
    db.add(collection)
    await _apply_default_collection(db, user.id, collection)
    record_audit_event(
        db,
        user_id=user.id,
        action="collection.create",
        resource_type="collection",
        resource_id=str(collection.id),
        metadata={"channel_ids": [str(channel.id) for channel in channels]},
    )
    await db.commit()
    await db.refresh(collection)
    channel_ids = await _collection_channel_ids(db, collection)
    return _collection_response(collection, channel_ids)


@router.get("/compare")
async def compare_collections(
    collection_ids: List[UUID] = Query(...),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    results = []
    for collection_id in collection_ids:
        collection, _ = await _get_collection_for_user(db, collection_id, user.id)
        await db.refresh(collection, attribute_names=["channels"])
        channel_ids = await _collection_channel_ids(db, collection)
        if not channel_ids:
            results.append(
                {
                    "collection_id": str(collection.id),
                    "name": collection.name,
                    "message_count_7d": 0,
                    "channel_count": 0,
                    "duplicate_rate": 0.0,
                }
            )
            continue

        week_ago = datetime.utcnow() - timedelta(days=7)
        total_result = await db.execute(
            select(func.count())
            .select_from(Message)
            .where(Message.channel_id.in_(channel_ids))
            .where(Message.published_at >= week_ago)
        )
        duplicates_result = await db.execute(
            select(func.count())
            .select_from(Message)
            .where(Message.channel_id.in_(channel_ids))
            .where(Message.published_at >= week_ago)
            .where(Message.is_duplicate == True)
        )
        total = total_result.scalar() or 0
        duplicates = duplicates_result.scalar() or 0
        results.append(
            {
                "collection_id": str(collection.id),
                "name": collection.name,
                "message_count_7d": total,
                "channel_count": len(channel_ids),
                "duplicate_rate": round(duplicates / total, 3) if total else 0.0,
            }
        )

    return {"comparisons": results}


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    await db.refresh(collection, attribute_names=["channels"])
    channel_ids = await _collection_channel_ids(db, collection)
    return _collection_response(collection, channel_ids)


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    payload: CollectionUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, permission = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id and permission not in {"editor", "admin"}:
        raise HTTPException(status_code=403, detail="Not authorized to update this collection")
    if collection.user_id != user.id:
        restricted_fields = [
            payload.is_default,
            payload.is_global,
            payload.parent_id,
            payload.auto_assign_languages,
            payload.auto_assign_keywords,
            payload.auto_assign_tags,
        ]
        if any(field is not None for field in restricted_fields):
            raise HTTPException(status_code=403, detail="Not authorized to change collection settings")
    await db.refresh(collection, attribute_names=["channels"])

    if payload.name is not None:
        collection.name = payload.name
    if payload.description is not None:
        collection.description = payload.description
    if payload.color is not None:
        collection.color = payload.color
    if payload.icon is not None:
        collection.icon = payload.icon
    if payload.is_default is not None:
        collection.is_default = payload.is_default
    if payload.is_global is not None:
        collection.is_global = payload.is_global
        if payload.is_global:
            collection.channels = []
    if payload.parent_id is not None:
        if payload.parent_id:
            await _get_collection_for_user(db, payload.parent_id, user.id)
        collection.parent_id = payload.parent_id
    if payload.auto_assign_languages is not None:
        collection.auto_assign_languages = payload.auto_assign_languages
    if payload.auto_assign_keywords is not None:
        collection.auto_assign_keywords = payload.auto_assign_keywords
    if payload.auto_assign_tags is not None:
        collection.auto_assign_tags = payload.auto_assign_tags
    if payload.channel_ids is not None:
        collection.channels = await _load_channels(db, payload.channel_ids)

    await _apply_default_collection(db, user.id, collection)
    record_audit_event(
        db,
        user_id=user.id,
        action="collection.update",
        resource_type="collection",
        resource_id=str(collection.id),
        metadata={"channel_ids": [str(channel.id) for channel in collection.channels]},
    )
    await db.commit()
    await db.refresh(collection)
    channel_ids = await _collection_channel_ids(db, collection)
    return _collection_response(collection, channel_ids)


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, permission = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id and permission != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this collection")

    await db.delete(collection)
    record_audit_event(
        db,
        user_id=user.id,
        action="collection.delete",
        resource_type="collection",
        resource_id=str(collection.id),
    )
    await db.commit()

    return {"message": "Collection deleted successfully"}


@router.get("/{collection_id}/stats", response_model=CollectionStatsResponse)
async def get_collection_stats(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    await db.refresh(collection, attribute_names=["channels"])
    channel_ids = await _collection_channel_ids(db, collection)
    if not channel_ids:
        return CollectionStatsResponse(
            message_count=0,
            message_count_24h=0,
            message_count_7d=0,
            channel_count=0,
            top_channels=[],
            activity_trend=[],
            duplicate_rate=0.0,
            languages={},
        )

    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    total_result = await db.execute(
        select(func.count()).select_from(Message).where(Message.channel_id.in_(channel_ids))
    )
    total = total_result.scalar() or 0

    last_day_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .where(Message.channel_id.in_(channel_ids))
        .where(Message.published_at >= day_ago)
    )
    last_week_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .where(Message.channel_id.in_(channel_ids))
        .where(Message.published_at >= week_ago)
    )
    duplicates_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .where(Message.channel_id.in_(channel_ids))
        .where(Message.is_duplicate == True)
    )

    top_channels_result = await db.execute(
        select(Channel.id, Channel.title, func.count(Message.id).label("count"))
        .join(Message, Message.channel_id == Channel.id)
        .where(Message.channel_id.in_(channel_ids))
        .group_by(Channel.id, Channel.title)
        .order_by(desc("count"))
        .limit(5)
    )
    top_channels = [
        {"channel_id": str(row.id), "channel_title": row.title, "count": row.count}
        for row in top_channels_result.all()
    ]

    date_bucket = func.date(Message.published_at)
    activity_result = await db.execute(
        select(date_bucket.label("day"), func.count().label("count"))
        .where(Message.channel_id.in_(channel_ids))
        .where(Message.published_at >= week_ago)
        .group_by(date_bucket)
        .order_by(date_bucket)
    )
    activity_trend = [{"date": str(row.day), "count": row.count} for row in activity_result.all()]

    languages_result = await db.execute(
        select(Message.source_language, func.count().label("count"))
        .where(Message.channel_id.in_(channel_ids))
        .where(Message.source_language.isnot(None))
        .where(Message.published_at >= week_ago)
        .group_by(Message.source_language)
    )
    languages = {row.source_language: row.count for row in languages_result.all() if row.source_language}

    duplicates = duplicates_result.scalar() or 0
    duplicate_rate = round(duplicates / total, 3) if total else 0.0

    return CollectionStatsResponse(
        message_count=total,
        message_count_24h=last_day_result.scalar() or 0,
        message_count_7d=last_week_result.scalar() or 0,
        channel_count=len(channel_ids),
        top_channels=top_channels,
        activity_trend=activity_trend,
        duplicate_rate=duplicate_rate,
        languages=languages,
    )


@router.post("/{collection_id}/digest", response_model=SummaryResponse)
async def generate_collection_digest(
    collection_id: UUID,
    user: User = Depends(current_active_user),
):
    filters = {"collections": [str(collection_id)]}
    summary = await generate_daily_summary(user_id=user.id, filters=filters, collection_id=collection_id)
    return summary


@router.get("/{collection_id}/digests", response_model=SummaryListResponse)
async def list_collection_digests(
    collection_id: UUID,
    limit: int = 10,
    offset: int = 0,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_collection_for_user(db, collection_id, user.id)
    query = (
        select(Summary)
        .where(Summary.user_id == user.id)
        .where(Summary.collection_id == collection_id)
        .order_by(desc(Summary.generated_at))
    )
    count_result = await db.execute(
        select(func.count())
        .select_from(Summary)
        .where(Summary.user_id == user.id)
        .where(Summary.collection_id == collection_id)
    )
    total = count_result.scalar() or 0
    result = await db.execute(query.limit(limit).offset(offset))
    summaries = result.scalars().all()
    return SummaryListResponse(
        summaries=summaries,
        total=total,
        page=offset // limit + 1,
        page_size=limit,
    )


@router.post("/{collection_id}/export")
async def export_collection_messages(
    collection_id: UUID,
    format: str = "csv",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(200, ge=1, le=1000),
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    await db.refresh(collection, attribute_names=["channels"])
    channel_ids = await _collection_channel_ids(db, collection)
    if not channel_ids:
        raise HTTPException(status_code=400, detail="Collection has no channels")

    query = select(Message, Channel).join(Channel)
    query = query.where(Message.channel_id.in_(channel_ids))
    if start_date:
        query = query.where(Message.published_at >= start_date)
    if end_date:
        query = query.where(Message.published_at <= end_date)

    if format == "csv":
        result = await db.execute(query.order_by(desc(Message.published_at)))
        rows = result.all()
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["collection", collection.name])
        writer.writerow(["description", collection.description or ""])
        writer.writerow(["channels", len(channel_ids)])
        writer.writerow([])
        writer.writerow([
            "message_id",
            "channel_title",
            "channel_username",
            "published_at",
            "original_text",
            "translated_text",
            "source_language",
            "target_language",
            "is_duplicate",
        ])
        for message, channel in rows:
            writer.writerow([
                str(message.id),
                channel.title,
                channel.username,
                message.published_at,
                message.original_text or "",
                message.translated_text or "",
                message.source_language or "",
                message.target_language or "",
                message.is_duplicate,
            ])
        output.seek(0)
        filename = f"telescope-collection-{collection_id}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if format == "html":
        result = await db.execute(query.order_by(desc(Message.published_at)).limit(limit))
        rows = result.all()
        from html import escape

        html_lines = [
            "<!DOCTYPE html>",
            "<html lang='fr'>",
            "<head><meta charset='utf-8'><title>TeleScope - Collection Export</title>",
            "<style>body{font-family:Arial,sans-serif;background:#f8fafc;color:#0f172a;padding:24px;}h1{font-size:20px;}article{margin:16px 0;padding:12px;border:1px solid #e2e8f0;border-radius:12px;background:#fff;}small{color:#64748b;}</style>",
            "</head><body>",
            f"<h1>Collection: {escape(collection.name)}</h1>",
        ]
        if collection.description:
            html_lines.append(f"<p>{escape(collection.description)}</p>")
        for message, channel in rows:
            html_lines.append("<article>")
            html_lines.append(
                f"<small>{escape(channel.title)} · {escape(channel.username)} · {message.published_at}</small>"
            )
            html_lines.append(f"<p>{escape(message.translated_text or message.original_text or '')}</p>")
            if message.translated_text and message.original_text:
                html_lines.append(f"<p><small>Original: {escape(message.original_text)}</small></p>")
            html_lines.append("</article>")
        html_lines.append("</body></html>")
        html = "\n".join(html_lines)
        return StreamingResponse(
            iter([html]),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=telescope-collection-{collection_id}.html"},
        )

    if format == "pdf":
        from fpdf import FPDF

        result = await db.execute(query.order_by(desc(Message.published_at)).limit(limit))
        rows = result.all()
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=14)
        pdf.cell(0, 10, f"TeleScope - {collection.name}", ln=True)
        pdf.set_font("Helvetica", size=11)
        for message, channel in rows:
            header = f"{channel.title} (@{channel.username}) - {message.published_at}"
            pdf.multi_cell(0, 8, header)
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(0, 6, message.translated_text or message.original_text or "")
            if message.translated_text and message.original_text:
                pdf.set_font("Helvetica", size=9)
                pdf.multi_cell(0, 6, f"Original: {message.original_text}")
            pdf.ln(2)
            pdf.set_font("Helvetica", size=11)

        output = pdf.output(dest="S")
        pdf_bytes = output.encode("latin-1", errors="ignore") if isinstance(output, str) else output
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=telescope-collection-{collection_id}.pdf",
            },
        )

    raise HTTPException(status_code=400, detail="Unsupported export format")


@router.get("/{collection_id}/shares", response_model=List[CollectionShareResponse])
async def list_collection_shares(
    collection_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view shares")
    result = await db.execute(select(CollectionShare).where(CollectionShare.collection_id == collection_id))
    return result.scalars().all()


@router.post("/{collection_id}/shares", response_model=CollectionShareResponse)
async def add_collection_share(
    collection_id: UUID,
    payload: CollectionShareCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to share this collection")
    result = await db.execute(
        select(CollectionShare)
        .where(CollectionShare.collection_id == collection_id)
        .where(CollectionShare.user_id == payload.user_id)
    )
    share = result.scalar_one_or_none()
    if share:
        share.permission = payload.permission
    else:
        share = CollectionShare(
            collection_id=collection_id,
            user_id=payload.user_id,
            permission=payload.permission,
        )
        db.add(share)
    await db.commit()
    await db.refresh(share)
    return share


@router.delete("/{collection_id}/shares/{share_user_id}")
async def delete_collection_share(
    collection_id: UUID,
    share_user_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    collection, _ = await _get_collection_for_user(db, collection_id, user.id)
    if collection.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to remove shares")
    result = await db.execute(
        select(CollectionShare)
        .where(CollectionShare.collection_id == collection_id)
        .where(CollectionShare.user_id == share_user_id)
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    await db.delete(share)
    await db.commit()
    return {"message": "Share removed"}
