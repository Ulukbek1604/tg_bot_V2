import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot_apps.handlers import rt,init_support_db
from bot_apps.db import init_db, close_db
from bot_apps.config_reader import TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Бот запущен")
    bot = Bot(token=TOKEN, parse_mode=None)
    dp = Dispatcher()
    dp.include_router(rt)

    await init_db()
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())