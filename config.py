import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    print(f"WARNING: .env file not found at {ENV_PATH}")
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'tournament.db')}")
OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")  # 'helloworld' = public demo key (ограничен); получи свой на ocr.space
