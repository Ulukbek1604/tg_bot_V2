import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot_apps.handlers import rt, init_support_db
from bot_apps.db import init_db, close_db, ensure_full_database_structure  # <-- ensure_sale_columns убрал тут
from bot_apps.config_reader import TOKEN
import aiosqlite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Либо оставляешь свою ensure_sale_columns здесь:
async def ensure_sale_columns():
    async with aiosqlite.connect('tg_bot.db') as db:
        cursor = await db.execute("PRAGMA table_info(steam_keys)")
        columns = [col[1] async for col in cursor]

        if 'sale_active' not in columns:
            await db.execute("ALTER TABLE steam_keys ADD COLUMN sale_active INTEGER DEFAULT 0")
        if 'sale_not' not in columns:
            await db.execute("ALTER TABLE steam_keys ADD COLUMN sale_not TEXT")
        if 'sale_ends_at' not in columns:
            await db.execute("ALTER TABLE steam_keys ADD COLUMN sale_ends_at TEXT")

        await db.commit()
        print("Колонки акций проверены и добавлены при необходимости")


async def main():
    logger.info("Бот запущен")
    bot = Bot(token=TOKEN, parse_mode=None)
    dp = Dispatcher()
    dp.include_router(rt)

    # --- порядок инициализаций БД ---
    await init_db()
    await ensure_full_database_structure()
    await ensure_sale_columns()
    await init_support_db()   # <<< ВАЖНО: инициализация таблицы tickets

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
