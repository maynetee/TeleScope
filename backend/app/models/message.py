from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean, ForeignKey, Index, SmallInteger, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import uuid


class Message(Base):
    __tablename__ = "messages"

    # Primary key as UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to channel (UUID)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), index=True, nullable=False)

    # Telegram message ID - BigInteger for large IDs
    telegram_message_id = Column(BigInteger, nullable=False)

    # Content
    original_text = Column(Text)
    translated_text = Column(Text, nullable=True)
    source_language = Column(String(10), nullable=True)
    target_language = Column(String(10), default="fr")

    # Media information (JSON - works with both SQLite and PostgreSQL)
    media_type = Column(String(50), nullable=True)  # photo, video, document, audio
    media_urls = Column(JSON, nullable=True)  # ["url1", "url2", ...]

    # Deduplication
    is_duplicate = Column(Boolean, default=False, index=True)
    originality_score = Column(SmallInteger, default=100)  # 0-100
    duplicate_group_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Vector store reference
    embedding_id = Column(String(255), nullable=True)

    # Named entities extracted (JSON - works with both SQLite and PostgreSQL)
    entities = Column(
        JSON,
        default={"persons": [], "locations": [], "organizations": []},
        nullable=True
    )

    # Timestamps with timezone
    published_at = Column(DateTime(timezone=True), index=True)
    fetched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    translated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    channel = relationship("Channel", back_populates="messages")

    # Composite indexes for common queries
    __table_args__ = (
        # Unique constraint: one message per channel
        Index("ix_messages_channel_telegram_id", "channel_id", "telegram_message_id", unique=True),
        # For timeline queries
        Index("ix_messages_channel_published", "channel_id", "published_at"),
        # For duplicate analysis
        Index("ix_messages_duplicate_group", "duplicate_group_id", postgresql_where=duplicate_group_id.isnot(None)),
    )
