import asyncio
from aiogram import Bot
from config import BOT_TOKEN, WEBAPP_URL

ALLOWED_UPDATES = ["message", "callback_query", "my_chat_member", "chat_member"]

async def main():
    bot = Bot(token=BOT_TOKEN)
    url = f"{WEBAPP_URL}/webhook"
    await bot.set_webhook(url=url, allowed_updates=ALLOWED_UPDATES)
    print(f"Webhook set to {url}")
    info = await bot.get_webhook_info()
    print(f"Webhook info: {info.url}")
    print(f"Allowed updates: {info.allowed_updates}")

if __name__ == "__main__":
    asyncio.run(main())
