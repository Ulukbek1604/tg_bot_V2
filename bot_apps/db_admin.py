import aiosqlite
import logging
from bot_apps.db import DB_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_admin(tg_id: int, name: str):
    """Добавляет нового администратора в базу данных."""
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            await db.execute('INSERT INTO admins (tg_id, name) VALUES (?, ?)', (tg_id, name))
            await db.commit()
            logger.info(f"Добавлен администратор: tg_id={tg_id}, name={name}")
            return True, f"Администратор '{name}' успешно добавлен."
    except aiosqlite.IntegrityError:
        logger.warning(f"Попытка добавить уже существующего администратора: tg_id={tg_id}")
        return False, f"Администратор с tg_id={tg_id} или именем '{name}' уже существует."
    except aiosqlite.Error as e:
        logger.error(f"Ошибка добавления администратора: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}"

async def remove_admin(tg_id: int):
    """Удаляет администратора из базы данных."""
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('DELETE FROM admins WHERE tg_id = ?', (tg_id,))
            await db.commit()
            if cursor.rowcount > 0:
                logger.info(f"Удалён администратор: tg_id={tg_id}")
                return True, f"Администратор с tg_id={tg_id} удалён."
            else:
                logger.warning(f"Администратор не найден: tg_id={tg_id}")
                return False, f"Администратор с tg_id={tg_id} не найден."
    except aiosqlite.Error as e:
        logger.error(f"Ошибка удаления администратора: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}"

async def is_admin(tg_id: int):
    """Проверяет, является ли пользователь администратором."""
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT tg_id FROM admins WHERE tg_id = ?', (tg_id,))
            result = await cursor.fetchone()
            logger.debug(f"Проверка администратора: tg_id={tg_id}, результат={result is not None}")
            return result is not None
    except aiosqlite.Error as e:
        logger.error(f"Ошибка проверки администратора: {str(e)}", exc_info=True)
        return False

async def get_admins():
    """Возвращает список всех администраторов."""
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT tg_id, name FROM admins')
            admins = await cursor.fetchall()
            if admins:
                admin_list = [f"ID: {admin['tg_id']}, Имя: {admin['name']}" for admin in admins]
                logger.info("Список администраторов успешно получен")
                return True, "Список администраторов:", admin_list
            else:
                logger.info("Администраторы не найдены")
                return True, "Администраторы не найдены.", []
    except aiosqlite.Error as e:
        logger.error(f"Ошибка получения списка администраторов: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}", []