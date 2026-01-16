from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class CollectionShareBase(BaseModel):
    user_id: UUID
    permission: str = "viewer"


class CollectionShareCreate(CollectionShareBase):
    pass


class CollectionShareResponse(CollectionShareBase):
    collection_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
