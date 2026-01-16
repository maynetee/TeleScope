"""Telegram message collector with Flood Wait handling.

This module provides a collector class for fetching messages and channel info
from Telegram channels, with built-in rate limiting and exponential backoff
for handling FloodWaitErrors.
"""
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import FloodWaitError, SlowModeWaitError
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import asyncio
import logging

from app.config import get_settings
from app.utils.retry import telegram_retry

logger = logging.getLogger(__name__)
settings = get_settings()

# Global lock to prevent concurrent Telegram session access
# Telethon uses SQLite for session storage, which doesn't handle concurrent writes well
_telegram_lock = asyncio.Lock()


class TelegramCollector:
    """Collector for fetching Telegram channel data with rate limiting.

    This class provides methods to fetch channel metadata and messages from
    Telegram channels. All methods use the @telegram_retry decorator to handle
    FloodWaitErrors with exponential backoff.

    Example:
        collector = TelegramCollector()
        try:
            channel_info = await collector.get_channel_info("durov")
            messages = await collector.get_recent_messages("durov", limit=20)
        finally:
            await collector.disconnect()
    """

    def __init__(self):
        self.api_id = settings.telegram_api_id
        self.api_hash = settings.telegram_api_hash
        self.phone = settings.telegram_phone
        self.client: Optional[TelegramClient] = None

    @staticmethod
    def _extract_message_data(message) -> dict | None:
        """Extract message data from a Telegram message object.

        Returns None if the message has no text content.
        """
        if not message.text:
            return None

        media_type = None
        media_urls = []

        if message.media:
            if hasattr(message.media, 'photo'):
                media_type = 'photo'
            elif hasattr(message.media, 'document'):
                media_type = 'document'
            elif hasattr(message.media, 'video'):
                media_type = 'video'

        return {
            'message_id': message.id,
            'text': message.text,
            'date': message.date,
            'media_type': media_type,
            'media_urls': media_urls,
        }

    async def connect(self):
        """Initialize and connect Telegram client."""
        if not self.client:
            # Store session files in data directory
            os.makedirs("data", exist_ok=True)
            self.client = TelegramClient("data/telegram_session", self.api_id, self.api_hash)
            await self.client.start(phone=self.phone)
            logger.info("Telegram client connected")
        return self.client

    async def disconnect(self):
        """Disconnect Telegram client."""
        if self.client:
            await self.client.disconnect()
            self.client = None
            logger.info("Telegram client disconnected")

    @telegram_retry
    async def get_channel_info(self, username: str) -> dict:
        """Fetch channel metadata from Telegram.

        Uses global lock to prevent concurrent session access.
        Automatically retries on FloodWaitError with exponential backoff.

        Args:
            username: Channel username (with or without @)

        Returns:
            Dict with channel info (id, title, username, description, participants_count)

        Raises:
            Exception: If channel cannot be fetched after retries
        """
        async with _telegram_lock:
            await self.connect()

            # Remove @ if present
            username = username.lstrip('@')

            logger.info(f"Fetching channel info for: {username}")

            # Get channel entity
            entity = await self.client.get_entity(username)

            # Get full channel info
            full_channel = await self.client(GetFullChannelRequest(entity))

            logger.info(f"Successfully fetched channel info for: {username}")

            return {
                'id': entity.id,
                'title': entity.title,
                'username': entity.username or username,
                'description': full_channel.full_chat.about or '',
                'participants_count': full_channel.full_chat.participants_count or 0,
            }

    @telegram_retry
    async def get_recent_messages(self, username: str, limit: int = 50, offset_date=None) -> list:
        """Fetch recent messages from a channel.

        Uses global lock to prevent concurrent session access.
        Automatically retries on FloodWaitError with exponential backoff.

        Args:
            username: Channel username (with or without @)
            limit: Maximum number of messages to fetch
            offset_date: Optional datetime to start fetching from

        Returns:
            List of message dicts with id, text, date, media_type, media_urls
        """
        async with _telegram_lock:
            await self.connect()

            username = username.lstrip('@')
            logger.info(f"Fetching {limit} recent messages from: {username}")

            entity = await self.client.get_entity(username)

            messages = []
            async for message in self.client.iter_messages(entity, limit=limit, offset_date=offset_date):
                msg_data = self._extract_message_data(message)
                if msg_data:
                    messages.append(msg_data)

            logger.info(f"Fetched {len(messages)} messages from: {username}")
            return messages

    @telegram_retry
    async def get_messages_since(self, username: str, days: int = 7, max_messages: int = 500) -> list:
        """Fetch messages from the last N days.

        Uses global lock to prevent concurrent session access.
        Automatically retries on FloodWaitError with exponential backoff.

        Args:
            username: Channel username (with or without @)
            days: Number of days to look back
            max_messages: Maximum number of messages to fetch

        Returns:
            List of message dicts with id, text, date, media_type, media_urls
        """
        async with _telegram_lock:
            await self.connect()

            username = username.lstrip('@')
            logger.info(f"Fetching messages from last {days} days for: {username}")

            entity = await self.client.get_entity(username)

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            messages = []

            async for message in self.client.iter_messages(entity, limit=max_messages):
                # Stop if message is older than cutoff
                msg_date = message.date
                if msg_date.tzinfo is None:
                    msg_date = msg_date.replace(tzinfo=timezone.utc)
                if msg_date < cutoff_date:
                    break

                msg_data = self._extract_message_data(message)
                if msg_data:
                    messages.append(msg_data)

            logger.info(f"Fetched {len(messages)} messages from last {days} days for: {username}")
            return messages
