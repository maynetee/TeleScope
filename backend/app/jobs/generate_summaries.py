from datetime import datetime
from app.services.summarizer import generate_daily_summary


async def generate_summaries_job():
    """
    Background job to generate daily summaries.

    Note: generate_daily_summary now manages its own DB sessions internally
    to avoid holding locks during the slow LLM API call.
    """
    print(f"[{datetime.utcnow()}] Starting summary generation job...")

    try:
        summary = await generate_daily_summary()
        print(f"Generated daily summary (ID: {summary.id}) with {summary.message_count} messages")
        print(f"Summary preview: {summary.content[:200]}...")

    except Exception as e:
        print(f"Error generating summary: {e}")

    print(f"[{datetime.utcnow()}] Summary generation job completed")
