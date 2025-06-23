import aiosqlite
import logging
from datetime import datetime
from bot_apps.db import DB_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_steam_key_into_db(game_name: str, st_key: str, price: int, count: int, genre: str, country: str):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            await db.execute('''
                INSERT INTO steam_keys (game_name, st_key, price, count, genre, country)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (game_name, st_key, price, count, genre, country))
            await db.commit()
            logger.info(f"Добавлен ключ: {game_name}, цена={price}, количество={count}")
            return True, f"Ключ для '{game_name}' успешно добавлен."
    except aiosqlite.Error as e:
        logger.error(f"Ошибка добавления ключа: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}"

async def edit_steam_key_into_db(key_id: int, game_name: str = None, st_key: str = None, price: int = None,
                                count: int = None, discount: int = None, genre: str = None, country: str = None):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            updates = []
            params = []
            if game_name is not None:
                updates.append("game_name = ?")
                params.append(game_name)
            if st_key is not None:
                updates.append("st_key = ?")
                params.append(st_key)
            if price is not None:
                updates.append("price = ?")
                params.append(price)
            if count is not None:
                updates.append("count = ?")
                params.append(count)
            if discount is not None:
                updates.append("discount = ?")
                params.append(discount)
            if genre is not None:
                updates.append("genre = ?")
                params.append(genre)
            if country is not None:
                updates.append("country = ?")
                params.append(country)
            if not updates:
                return False, "Не указаны параметры для обновления."
            params.append(key_id)
            query = f"UPDATE steam_keys SET {', '.join(updates)} WHERE id = ?"
            cursor = await db.execute(query, params)
            await db.commit()
            if cursor.rowcount > 0:
                logger.info(f"Обновлён ключ: id={key_id}")
                return True, f"Ключ с ID={key_id} успешно обновлён."
            else:
                logger.warning(f"Ключ не найден: id={key_id}")
                return False, f"Ключ с ID={key_id} не найден."
    except aiosqlite.Error as e:
        logger.error(f"Ошибка обновления ключа: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}"

async def delete_steam_key_from_db(key_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('DELETE FROM steam_keys WHERE id = ?', (key_id,))
            await db.commit()
            if cursor.rowcount > 0:
                logger.info(f"Удалён ключ: id={key_id}")
                return True, f"Ключ с ID={key_id} удалён."
            else:
                logger.warning(f"Ключ не найден: id={key_id}")
                return False, f"Ключ с ID={key_id} не найден."
    except aiosqlite.Error as e:
        logger.error(f"Ошибка удаления ключа: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}"

async def show_all_games(genre: str = None, max_price: int = None):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            query = 'SELECT * FROM steam_keys WHERE count > 0'
            params = []
            if genre:
                query += ' AND genre = ?'
                params.append(genre)
            if max_price is not None:
                query += ' AND price <= ?'
                params.append(max_price)
            cursor = await db.execute(query, params)
            games = await cursor.fetchall()
            logger.debug(f"Запрос выполнен: {query}, params={params}, найдено записей: {len(games)}")
            if games:
                game_list = [
                    f"*ID*: {game['id']}\n*Игра*: {game['game_name']}\n*Цена*: {game['price']}$\n*Скидка*: {game['discount']}%\n*Жанр*: {game['genre']}\n*Страна*: {game['country']}\n*В наличии*: {game['count']}"
                    for game in games
                ]
                logger.info(f"Найдено игр: {len(games)}")
                return True, f"Найдено {len(games)} игр:", game_list
            else:
                logger.info("Игры не найдены")
                return True, "Игры не найдены.", []
    except aiosqlite.Error as e:
        logger.error(f"Ошибка получения списка игр: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}", []

async def search_games(search_text: str):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM steam_keys 
                WHERE game_name LIKE ? AND count > 0
            ''', (f'%{search_text}%',))
            games = await cursor.fetchall()
            if games:
                game_list = [
                    f"*ID*: {game['id']}\n*Игра*: {game['game_name']}\n*Цена*: {game['price']}$\n*Скидка*: {game['discount']}%\n*Жанр*: {game['genre']}\n*Страна*: {game['country']}\n*В наличии*: {game['count']}"
                    for game in games
                ]
                logger.info(f"Найдено игр по запросу '{search_text}': {len(games)}")
                return True, f"Найдено {len(games)} игр:", game_list
            else:
                logger.info(f"Игры не найдены по запросу '{search_text}'")
                return True, f"Игры по запросу '{search_text}' не найдены.", []
    except aiosqlite.Error as e:
        logger.error(f"Ошибка поиска игр: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}", []

async def create_order(user_id: int, key_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT game_name, count FROM steam_keys WHERE id = ?', (key_id,))
            game = await cursor.fetchone()
            if not game or game['count'] <= 0:
                logger.warning(f"Ключ не найден или закончился: key_id={key_id}")
                return False, f"Ключ с ID={key_id} не найден или закончился.", None
            game_name = game['game_name']
            order_date = datetime.now().isoformat()
            await db.execute('''
                INSERT INTO orders (user_id, key_id, status, order_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, key_id, 'pending', order_date))
            await db.execute('UPDATE steam_keys SET count = count - 1 WHERE id = ?', (key_id,))
            await db.commit()
            logger.info(f"Создан заказ: user_id={user_id}, key_id={key_id}, game={game_name}")
            return True, f"Заказ на '{game_name}' создан. Ожидайте подтверждения.", game_name
    except aiosqlite.Error as e:
        logger.error(f"Ошибка создания заказа: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}", None

async def complete_order(order_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT orders.id, steam_keys.game_name 
                FROM orders 
                JOIN steam_keys ON orders.key_id = steam_keys.id 
                WHERE orders.id = ? AND orders.status = ?
            ''', (order_id, 'pending'))
            order = await cursor.fetchone()
            if not order:
                logger.warning(f"Заказ не найден или уже обработан: order_id={order_id}")
                return False, f"Заказ с ID={order_id} не найден или уже обработан.", None
            game_name = order['game_name']
            await db.execute('UPDATE orders SET status = ? WHERE id = ?', ('completed', order_id))
            await db.commit()
            logger.info(f"Заказ завершён: order_id={order_id}, game={game_name}")
            return True, f"Заказ на '{game_name}' завершён.", game_name
    except aiosqlite.Error as e:
        logger.error(f"Ошибка завершения заказа: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}", None

async def cancel_order(order_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT key_id FROM orders WHERE id = ? AND status = ?', (order_id, 'pending'))
            order = await cursor.fetchone()
            if not order:
                logger.warning(f"Заказ не найден или уже обработан: order_id={order_id}")
                return False, f"Заказ с ID={order_id} не найден или уже обработан."
            await db.execute('UPDATE orders SET status = ? WHERE id = ?', ('cancelled', order_id))
            await db.execute('UPDATE steam_keys SET count = count + 1 WHERE id = ?', (order['key_id'],))
            await db.commit()
            logger.info(f"Заказ отменён: order_id={order_id}")
            return True, f"Заказ с ID={order_id} отменён."
    except aiosqlite.Error as e:
        logger.error(f"Ошибка отмены заказа: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}"

async def get_orders():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT orders.id, orders.user_id, steam_keys.game_name, orders.status, orders.order_date
                FROM orders
                JOIN steam_keys ON orders.key_id = steam_keys.id
            ''')
            orders = await cursor.fetchall()
            if orders:
                order_list = [
                    f"*ID*: {order['id']}\n*Пользователь*: {order['user_id']}\n*Игра*: {order['game_name']}\n*Статус*: {order['status']}\n*Дата*: {order['order_date']}"
                    for order in orders
                ]
                logger.info(f"Найдено заказов: {len(orders)}")
                return True, f"Найдено {len(orders)} заказов:", order_list
            else:
                logger.info("Заказы не найдены")
                return True, "Заказы не найдены.", []
    except aiosqlite.Error as e:
        logger.error(f"Ошибка получения списка заказов: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}", []

async def get_analytics():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT COUNT(*) as order_count FROM orders')
            order_count = (await cursor.fetchone())['order_count']
            cursor = await db.execute('SELECT COUNT(*) as game_count FROM steam_keys WHERE count > 0')
            game_count = (await cursor.fetchone())['game_count']
            data = [
                f"Всего заказов: {order_count}",
                f"Игр в наличии: {game_count}"
            ]
            logger.info("Аналитика успешно получена")
            return True, "Аналитика:", data
    except aiosqlite.Error as e:
        logger.error(f"Ошибка получения аналитики: {str(e)}", exc_info=True)
        return False, f"Ошибка базы данных: {str(e)}", []