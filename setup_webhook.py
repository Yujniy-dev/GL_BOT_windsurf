import asyncio
from aiogram import Bot
from config import BOT_TOKEN, WEBAPP_URL

async def main():
    bot = Bot(token=BOT_TOKEN)
    url = f"{WEBAPP_URL}/webhook"
    await bot.set_webhook(url=url)
    print(f"Webhook set to {url}")
    info = await bot.get_webhook_info()
    print(f"Webhook info: {info.url}")

if __name__ == "__main__":
    asyncio.run(main())
