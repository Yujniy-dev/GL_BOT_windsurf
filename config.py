import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tournament.db")
