import aiosqlite
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def is_admin(tg_id: int) -> bool:
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            cursor = await db.execute('SELECT COUNT(*) FROM admins WHERE tg_id = ?', (tg_id,))
            count = (await cursor.fetchone())[0]
            return count > 0
    except aiosqlite.Error as e:
        logger.error(f"Ошибка при проверке админа: {str(e)}")
        return False

async def add_admin(tg_id: int, name: str):
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            await db.execute('INSERT OR IGNORE INTO admins (tg_id, name) VALUES (?, ?)', (tg_id, name))
            await db.commit()
            return True, f"Администратор {name} (ID: {tg_id}) добавлен."
    except Exception as e:
        return False, f"Ошибка при добавлении администратора: {e}"

async def remove_admin(tg_id: int):
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            cursor = await db.execute('SELECT name FROM admins WHERE tg_id = ?', (tg_id,))
            admin = await cursor.fetchone()
            if admin:
                await db.execute('DELETE FROM admins WHERE tg_id = ?', (tg_id,))
                await db.commit()
                return True, f"Администратор {admin[0]} (ID: {tg_id}) удалён."
            return False, "Администратор не найден."
    except Exception as e:
        return False, f"Ошибка при удалении администратора: {e}"

async def get_admins():
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT tg_id, name FROM admins')
            admins = await cursor.fetchall()
            if admins:
                admin_list = [f"ID: {admin['tg_id']} | Имя: {admin['name']}" for admin in admins]
                return True, "Список администраторов:", admin_list
            return True, "Список администраторов пуст.", []
    except Exception as e:
        return False, f"Произошла ошибка при загрузке списка администраторов: {e}"


async def get_global_order_stats():
    """
    Общая статистика по всем заказам.
    Возвращает: (success: bool, message: str, data: dict | None)
    """
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row

            # Основные цифры
            cursor = await db.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) AS confirmed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
                    SUM(CASE WHEN status = 'pending'   THEN 1 ELSE 0 END) AS pending
                FROM orders
                """
            )
            row = await cursor.fetchone()

            # Выручка по подтверждённым
            cursor = await db.execute(
                """
                SELECT
                    COALESCE(SUM(sk.price), 0) AS revenue
                FROM orders o
                JOIN steam_keys sk ON sk.id = o.key_id
                WHERE o.status = 'confirmed'
                """
            )
            rev_row = await cursor.fetchone()
            revenue = rev_row["revenue"]

            text = (
                "📊 Общая статистика заказов:\n"
                f"Всего заказов: {row['total']}\n"
                f"Подтверждено: {row['confirmed']}\n"
                f"Отменено: {row['cancelled']}\n"
                f"В ожидании: {row['pending']}\n"
                f"Выручка: {revenue}"
            )

            data = {
                "total": row["total"],
                "confirmed": row["confirmed"],
                "cancelled": row["cancelled"],
                "pending": row["pending"],
                "revenue": revenue,
            }

            return True, text, data

    except Exception as e:
        logger.error(f"Ошибка при получении общей статистики: {e}")
        return False, f"Ошибка при получении статистики: {e}", None


async def get_user_order_stats(user_id: int):
    """
    Статистика по конкретному пользователю (по его Telegram user_id).
    Возвращает: (success: bool, message: str, data: dict | None)
    """
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) AS confirmed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
                    SUM(CASE WHEN status = 'pending'   THEN 1 ELSE 0 END) AS pending
                FROM orders
                WHERE user_id = ?
                """,
                (user_id,)
            )
            row = await cursor.fetchone()

            # Сколько денег потратил пользователь (по подтверждённым заказам)
            cursor = await db.execute(
                """
                SELECT
                    COALESCE(SUM(sk.price), 0) AS spent
                FROM orders o
                JOIN steam_keys sk ON sk.id = o.key_id
                WHERE o.user_id = ?
                  AND o.status = 'confirmed'
                """,
                (user_id,)
            )
            spent_row = await cursor.fetchone()
            spent = spent_row["spent"]

            if row["total"] == 0:
                return True, "У этого пользователя ещё нет заказов.", None

            text = (
                f"📊 Статистика по пользователю {user_id}:\n"
                f"Всего заказов: {row['total']}\n"
                f"Подтверждено: {row['confirmed']}\n"
                f"Отменено: {row['cancelled']}\n"
                f"В ожидании: {row['pending']}\n"
                f"Всего потрачено: {spent}"
            )

            data = {
                "user_id": user_id,
                "total": row["total"],
                "confirmed": row["confirmed"],
                "cancelled": row["cancelled"],
                "pending": row["pending"],
                "spent": spent,
            }

            return True, text, data

    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователя: {e}")
        return False, f"Ошибка при получении статистики пользователя: {e}", None


async def get_daily_order_stats(limit: int = 7):
    """
    Статистика по дням (последние N дней).
    Возвращает: (success: bool, message: str, lines: list[str])
    """
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT
                    date(order_date) AS day,
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) AS confirmed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
                    SUM(CASE WHEN status = 'pending'   THEN 1 ELSE 0 END) AS pending
                FROM orders
                GROUP BY date(order_date)
                ORDER BY day DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = await cursor.fetchall()

            if not rows:
                return True, "Заказов пока нет.", []

            lines = []
            for r in rows:
                line = (
                    f"{r['day']}: всего {r['total']}, "
                    f"✅ {r['confirmed']}, ❌ {r['cancelled']}, ⏳ {r['pending']}"
                )
                lines.append(line)

            msg = "📅 Статистика по дням:\n" + "\n".join(lines)
            return True, msg, lines

    except Exception as e:
        logger.error(f"Ошибка при получении статистики по дням: {e}")
        return False, f"Ошибка при получении статистики по дням: {e}", []
async def get_users_overview():
    """
    Сводка по всем пользователям:
    user_id, количество заказов и разбор по статусам.
    Возвращает: (success: bool, message: str, lines: list[str])
    """
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row

            cursor = await db.execute(
                """
                SELECT
                    user_id,
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) AS confirmed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled,
                    SUM(CASE WHEN status = 'pending'   THEN 1 ELSE 0 END) AS pending
                FROM orders
                GROUP BY user_id
                ORDER BY total DESC
                """
            )
            rows = await cursor.fetchall()

            if not rows:
                return True, "Пока нет ни одного заказа.", []

            lines = []
            for r in rows:
                line = (
                    f"👤 {r['user_id']}: "
                    f"всего {r['total']}, "
                    f"✅ {r['confirmed']}, "
                    f"❌ {r['cancelled']}, "
                    f"⏳ {r['pending']}"
                )
                lines.append(line)

            msg = "📋 Статистика по пользователям:\n\n" + "\n".join(lines)
            return True, msg, lines

    except Exception as e:
        logger.error(f"Ошибка при получении сводки по пользователям: {e}")
        return False, f"Ошибка при получении сводки по пользователям: {e}", []
