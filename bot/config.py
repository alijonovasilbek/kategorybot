import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-webapp-url.com")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./shop.db")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

# Buyurtmalar uchun guruh chat ID (masalan: -1001234567890)
ORDER_GROUP_ID = int(os.getenv("ORDER_GROUP_ID", "0"))

# Admin panel uchun login/parol
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Do'kon markazi koordinatasi (yetkazib berish hisoblash uchun)
SHOP_LAT = float(os.getenv("SHOP_LAT", "41.299496"))
SHOP_LNG = float(os.getenv("SHOP_LNG", "69.240073"))

# Yetkazib berish narxi (so'm/km)
DELIVERY_PRICE_PER_KM = float(os.getenv("DELIVERY_PRICE_PER_KM", "2000"))
DELIVERY_FREE_DISTANCE_KM = float(os.getenv("DELIVERY_FREE_DISTANCE_KM", "3"))
