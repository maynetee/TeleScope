from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.summary import Summary
from app.models.user import User
from app.schemas.summary import SummaryResponse, SummaryGenerateRequest
from app.services.summarizer import generate_daily_summary
from app.auth.users import current_active_user

router = APIRouter()


@router.get("/daily", response_model=SummaryResponse)
async def get_daily_summary(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest daily summary.

    Requires authentication.
    """
    result = await db.execute(
        select(Summary)
        .where(Summary.digest_type == "daily")
        .order_by(desc(Summary.generated_at))
        .limit(1)
    )
    summary = result.scalar_one_or_none()

    if not summary:
        raise HTTPException(status_code=404, detail="No daily summary found")

    return summary


@router.post("/generate", response_model=SummaryResponse)
async def generate_summary(
    request: SummaryGenerateRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger summary generation.

    Requires authentication.
    """
    if request.summary_type == "daily":
        summary = await generate_daily_summary(db, user_id=user.id)
        return summary
    else:
        raise HTTPException(status_code=400, detail="Unsupported summary type")
