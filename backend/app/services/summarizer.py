import httpx
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.models.message import Message
from app.models.summary import Summary
from app.models.channel import Channel

settings = get_settings()


class SummarizerService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def generate_summary(self, messages: list[dict]) -> str:
        """
        Generate a summary using OpenRouter API

        Args:
            messages: List of message dicts with 'text' and 'channel' keys

        Returns:
            Generated summary text
        """
        if not messages:
            return "No messages to summarize."

        # Prepare context
        context = "Here are the recent messages from various Telegram channels:\n\n"
        for msg in messages[:50]:  # Limit to 50 messages to avoid token limits
            context += f"[{msg['channel']}]: {msg['text'][:500]}\n\n"

        # Create prompt
        prompt = f"""{context}

Please provide a concise summary (3-5 sentences) of the key information and events from these messages. Focus on:
1. Main topics and themes
2. Important events or announcements
3. Notable trends or patterns

Keep the summary clear, factual, and well-organized."""

        # Call OpenRouter API
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()

                summary = result['choices'][0]['message']['content']
                return summary.strip()
            except Exception as e:
                print(f"Summary generation failed: {e}")
                return f"Failed to generate summary: {str(e)}"


async def generate_daily_summary(db: AsyncSession = None) -> Summary:
    """
    Generate daily summary for the last 24 hours.

    IMPORTANT: This function releases the database lock during the LLM API call
    to prevent blocking other database operations. It uses short-lived sessions
    for reading and writing data.

    Args:
        db: Deprecated, no longer used. Kept for backward compatibility.

    Returns:
        Created Summary object
    """
    from app.database import AsyncSessionLocal

    # Step 1: Get messages from last 24 hours (short DB session)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Message, Channel)
            .join(Channel)
            .where(Message.published_at >= start_time)
            .where(Message.published_at <= end_time)
            .where(Message.is_duplicate == False)  # Exclude duplicates
        )
        rows = result.all()

        # Prepare messages for summarization (extract data before closing session)
        messages_data = [
            {
                'text': msg.translated_text or msg.original_text,
                'channel': channel.title
            }
            for msg, channel in rows
        ]

    # Step 2: Generate summary via LLM API (NO DB session held - this is slow)
    summarizer = SummarizerService()
    summary_content = await summarizer.generate_summary(messages_data)

    # Step 3: Save summary to DB (short DB session)
    async with AsyncSessionLocal() as session:
        summary = Summary(
            summary_type='daily',
            content=summary_content,
            message_count=len(messages_data),
            period_start=start_time,
            period_end=end_time,
        )

        session.add(summary)
        await session.commit()
        await session.refresh(summary)

        return summary
