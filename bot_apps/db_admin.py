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



