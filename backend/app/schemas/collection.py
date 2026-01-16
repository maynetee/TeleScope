from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: bool = False
    is_global: bool = False
    parent_id: Optional[UUID] = None
    auto_assign_languages: Optional[List[str]] = None
    auto_assign_keywords: Optional[List[str]] = None
    auto_assign_tags: Optional[List[str]] = None


class CollectionCreate(CollectionBase):
    channel_ids: Optional[List[UUID]] = None


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    channel_ids: Optional[List[UUID]] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: Optional[bool] = None
    is_global: Optional[bool] = None
    parent_id: Optional[UUID] = None
    auto_assign_languages: Optional[List[str]] = None
    auto_assign_keywords: Optional[List[str]] = None
    auto_assign_tags: Optional[List[str]] = None


class CollectionResponse(CollectionBase):
    id: UUID
    user_id: UUID
    channel_ids: List[UUID] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionStatsResponse(BaseModel):
    message_count: int
    message_count_24h: int
    message_count_7d: int
    channel_count: int
    top_channels: List[dict]
    activity_trend: List[dict]
    duplicate_rate: float
    languages: dict
