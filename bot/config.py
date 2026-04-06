import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-webapp-url.com")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./shop.db")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
