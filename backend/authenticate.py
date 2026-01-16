"""
Script to authenticate Telegram session interactively
"""
import asyncio
from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')
PHONE = os.getenv('TELEGRAM_PHONE', '')

async def main():
    print(f"Authenticating Telegram for phone: {PHONE}")
    print(f"API ID: {API_ID}")

    # Create data directory if needed
    os.makedirs('data', exist_ok=True)

    client = TelegramClient('data/telegram_session', API_ID, API_HASH)

    await client.start(phone=PHONE)

    if await client.is_user_authorized():
        print("\n✅ Authentication successful!")
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} {me.last_name or ''}")
        print(f"Phone: {me.phone}")
    else:
        print("\n❌ Authentication failed")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
