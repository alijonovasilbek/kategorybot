# KategoryBot

Telegram WebApp do'kon boti. Repo ichida:

- `bot/` - aiogram bot
- `api.py` - FastAPI backend
- `database/` - SQLAlchemy modellari va CRUD
- `webapp/` - foydalanuvchi va admin sahifalari

## Docker

1. `.env.example` dan `.env` yarating.
2. `.env` ichida kamida quyidagilarni to'ldiring:

```env
BOT_TOKEN=your_bot_token_here
WEBAPP_URL=https://your-domain.com
ADMIN_IDS=123456789
POSTGRES_PASSWORD=change-this-password
```

3. Loyihani ishga tushiring:

```bash
docker compose up --build -d
```

4. Demo ma'lumot kerak bo'lsa:

```bash
docker compose exec app python seed.py
```

5. To'xtatish:

```bash
docker compose down
```

`app` servisi bot va API ni bitta container ichida `run.py` orqali ishga tushiradi. `db` servisi PostgreSQL.

## Muhim env lar

```env
DATABASE_URL=postgresql+asyncpg://kategorybot:kategorybot@db:5432/kategorybot
POSTGRES_DB=kategorybot
POSTGRES_USER=kategorybot
POSTGRES_PASSWORD=change-this-password
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
ORDER_GROUP_ID=-1001234567890
SHOP_LAT=41.299496
SHOP_LNG=69.240073
DELIVERY_PRICE_PER_KM=2000
DELIVERY_FREE_DISTANCE_KM=3
```

## Lokal ishga tushirish

```bash
pip install -r requirements.txt
python run.py
```
