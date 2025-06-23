import asyncio
import aiosqlite
from bot_apps.db import DB_NAME
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_test_data():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            # Добавляем администратора
            await db.execute("INSERT OR IGNORE INTO admins (id, tg_id, name) VALUES (?, ?, ?)",
                             (1, 1155154067, "Test Admin"))

            # Добавляем игры
            await db.execute("""
                             INSERT OR IGNORE INTO steam_keys (game_name, st_key, price, count, genre, discount, country)
                             VALUES (?, ?, ?, ?, ?, ?, ?)
                             """, ("Test Game 1", "TESTKEY1", 10, 10, "Action", 0,"Global"))
            await db.execute("""
                INSERT OR REPLACE INTO steam_keys (id, game_name, st_key, price, count, genre, discount, country)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (2, "Test Game 2", "TESTKEY2", 20, 5, "ActionRPG", 10, "Global"))
            await db.execute("""
                             INSERT OR IGNORE INTO steam_keys (game_name, st_key, price, count, genre, discount, country)
                             VALUES (?, ?, ?, ?, ?, ?, ?)
                             """, ("GTA V", "TESTKEY3", 30, 3, "Action", "Global", 20))

            # Добавляем заказ
            await db.execute("""
                             INSERT OR IGNORE INTO orders (id, user_id, key_id, status, order_date)
                             VALUES (?, ?, ?, ?, ?)
                             """, (1, 1155154067, 1, "pending", "2025-06-23T10:00:00"))

            # Добавляем тикет поддержки
            await db.execute("""
                             INSERT OR IGNORE INTO support_tickets (ticket_id, user_id, message, status, ticket_time)
                             VALUES (?, ?, ?, ?, ?)
                             """, (1, 1155154067, "Test issue with game", "open", "2025-06-23T10:30:00"))

            await db.commit()
            logger.info("Тестовые данные успешно созданы")

    except aiosqlite.Error as e:
        logger.error(f"Ошибка создания тестовых данных: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(create_test_data())