"""
run.py — Bot va API ni bitta jarayonda ishga tushirish
Deployment uchun qulay (Railway, VPS va boshqalar)
"""
import asyncio
import threading
import logging
import os
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def run_api():
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🌐 API ishga tushmoqda: port {port}")
    uvicorn.run("api:app", host="0.0.0.0", port=port, log_level="warning")


async def run_bot():
    from aiogram import Bot, Dispatcher
    from aiogram.fsm.storage.memory import MemoryStorage
    from bot.config import BOT_TOKEN
    from bot.handlers import router
    from database.db import init_db

    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    logger.info("🤖 Bot ishga tushmoqda...")
    await dp.start_polling(bot, skip_updates=True)


def main():
    # API ni alohida thread da ishga tushir
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info("✅ API thread boshlandi")

    # Botni asosiy event loop da ishga tushir
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
