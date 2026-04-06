import asyncio
import logging
import os

import uvicorn


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_api():
    port = int(os.getenv("PORT", 8000))
    logger.info("API ishga tushmoqda: port %s", port)
    config = uvicorn.Config("api:app", host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()


async def run_bot():
    from aiogram import Bot, Dispatcher
    from aiogram.fsm.storage.memory import MemoryStorage

    from bot.handlers import router
    from config import BOT_TOKEN
    from database.db import init_db

    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    logger.info("Bot ishga tushmoqda...")
    await dispatcher.start_polling(bot, skip_updates=True)


async def main():
    api_task = asyncio.create_task(run_api(), name="api")
    bot_task = asyncio.create_task(run_bot(), name="bot")
    logger.info("API va bot tasklari boshlandi")

    done, pending = await asyncio.wait({api_task, bot_task}, return_when=asyncio.FIRST_EXCEPTION)

    for task in pending:
        task.cancel()

    for task in done:
        exc = task.exception()
        if exc:
            raise exc


if __name__ == "__main__":
    asyncio.run(main())
