import aiosqlite
import html
import logging

logger = logging.getLogger(__name__)

async def add_steam_key_into_db(game_name, st_key, price, count, genre=None, region=None, image_urls=None):
    """Добавляет Steam ключ в базу данных."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            await db.execute('''
                             INSERT INTO steam_keys (game_name, st_key, price, count, genre, region, image_urls)
                             VALUES (?, ?, ?, ?, ?, ?, ?)
                             ''', (game_name, st_key, price, count, genre, region, image_urls))
            await db.commit()
            logger.info(f"Добавлена игра: {game_name}, ключ: {st_key}, цена: {price}, количество: {count}")
            return True, "Игра успешно добавлена."
    except Exception as e:
        logger.error(f"Ошибка добавления ключа в базу данных: {e}", exc_info=True)
        return False, f"Ошибка добавления игры: {str(e)}"

async def edit_steam_key_into_db(game_id, game_name=None, st_key=None, price=None, count=None, discount=None,
                                 genre=None, region=None, image_urls=None):
    """Редактирует Steam ключ в базе данных, обновляя только указанные параметры."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM steam_keys WHERE id = ?', (game_id,))
            game = await cursor.fetchone()
            if not game:
                logger.warning(f"Игра с ID {game_id} не найдена")
                return False, "Игра с таким ID не найдена."

            updates = []
            params = []
            if game_name is not None and game_name != '':
                updates.append("game_name = ?")
                params.append(game_name)
            if st_key is not None and st_key != '':
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
            if genre is not None and genre != '':
                updates.append("genre = ?")
                params.append(genre)
            if region is not None and region != '':
                updates.append("region = ?")
                params.append(region)
            if image_urls is not None and image_urls != '':
                updates.append("image_urls = ?")
                params.append(image_urls)

            if not updates:
                logger.warning("Не указаны параметры для обновления")
                return False, "Не указаны параметры для обновления."

            params.append(game_id)
            query = f"UPDATE steam_keys SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, params)
            await db.commit()
            logger.info(f"Игра с ID {game_id} успешно обновлена: {updates}")
            return True, "Игра успешно обновлена."
    except Exception as e:
        logger.error(f"Ошибка редактирования ключа: {e}", exc_info=True)
        return False, f"Ошибка редактирования игры: {str(e)}"

async def delete_steam_key_from_db(game_id):
    """Удаляет Steam ключ из базы данных."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            cursor = await db.execute('SELECT * FROM steam_keys WHERE id = ?', (game_id,))
            game = await cursor.fetchone()
            if not game:
                logger.warning(f"Игра с ID {game_id} не найдена")
                return False, "Игра с таким ID не найдена."
            await db.execute('DELETE FROM steam_keys WHERE id = ?', (game_id,))
            await db.commit()
            logger.info(f"Игра с ID {game_id} успешно удалена")
            return True, "Игра успешно удалена."
    except Exception as e:
        logger.error(f"Ошибка удаления ключа: {e}", exc_info=True)
        return False, f"Ошибка удаления игры: {str(e)}"

async def show_all_games():
    """Возвращает список всех доступных игр."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM steam_keys WHERE count > 0')
            games = await cursor.fetchall()
            if not games:
                logger.info("Игры не найдены в базе данных")
                return False, "Игры не найдены.", []

            result = []
            for game in games:
                price = game['price']
                discount = game['discount'] or 0
                final_price = price * (1.0 - discount / 100.0)
                game_text = (
                    f"*ID*: {game['id']}\n"
                    f"*Игра*: {game['game_name']}\n"
                    f"*Цена*: ${final_price:.2f}\n"
                    f"*Скидка*: {discount}%\n"
                    f"*Жанр*: {game['genre'] or 'Не указан'}\n"
                    f"*Регион*: {game['region'] or 'Не указан'}"
                )
                result.append({
                    'text': game_text,
                    'image_urls': game['image_urls'] or ''
                })
            logger.info(f"Найдено {len(games)} игр")
            return True, "Игры найдены.", result
    except Exception as e:
        logger.error(f"Ошибка получения списка игр: {e}", exc_info=True)
        return False, f"Ошибка получения игр: {str(e)}", []

async def filter_games_by_price(price_limit):
    """Фильтрует игры по цене с учётом скидок."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM steam_keys 
                WHERE count > 0 AND (price * (1.0 - discount / 100.0)) <= ?
            ''', (float(price_limit),))
            games = await cursor.fetchall()
            if not games:
                logger.info(f"Игры с ценой до ${price_limit} не найдены")
                return False, f"Игры с ценой до ${price_limit} не найдены.", []

            result = []
            for game in games:
                price = game['price']
                discount = game['discount'] or 0
                final_price = price * (1.0 - discount / 100.0)
                game_text = (
                    f"*ID*: {game['id']}\n"
                    f"*Игра*: {game['game_name']}\n"
                    f"*Цена*: ${final_price:.2f}\n"
                    f"*Скидка*: {discount}%\n"
                    f"*Жанр*: {game['genre'] or 'Не указан'}\n"
                    f"*Регион*: {game['region'] or 'Не указан'}"
                )
                result.append({
                    'text': game_text,
                    'image_urls': game['image_urls'] or ''
                })
            logger.info(f"Найдено {len(games)} игр с ценой до ${price_limit}")
            return True, f"Игры с ценой до ${price_limit} найдены.", result
    except Exception as e:
        logger.error(f"Ошибка фильтрации игр по цене: {e}", exc_info=True)
        return False, f"Ошибка фильтрации игр: {str(e)}", []

async def filter_games_by_genre(genre):
    """Фильтрует игры по жанру."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM steam_keys 
                WHERE count > 0 AND genre = ?
            ''', (genre,))
            games = await cursor.fetchall()
            if not games:
                logger.info(f"Игры жанра '{genre}' не найдены")
                return False, f"Игры жанра '{genre}' не найдены.", []

            result = []
            for game in games:
                price = game['price']
                discount = game['discount'] or 0
                final_price = price * (1.0 - discount / 100.0)
                game_text = (
                    f"*ID*: {game['id']}\n"
                    f"*Игра*: {game['game_name']}\n"
                    f"*Цена*: ${final_price:.2f}\n"
                    f"*Скидка*: {discount}%\n"
                    f"*Жанр*: {game['genre'] or 'Не указан'}\n"
                    f"*Регион*: {game['region'] or 'Не указан'}"
                )
                result.append({
                    'text': game_text,
                    'image_urls': game['image_urls'] or ''
                })
            logger.info(f"Найдено {len(games)} игр жанра '{genre}'")
            return True, f"Игры жанра '{genre}' найдены.", result
    except Exception as e:
        logger.error(f"Ошибка фильтрации игр по жанру: {e}", exc_info=True)
        return False, f"Ошибка фильтрации игр: {str(e)}", []

async def search_games(query):
    """Поиск игр по названию."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM steam_keys WHERE game_name LIKE ? AND count > 0', (f'%{query}%',))
            games = await cursor.fetchall()
            if not games:
                logger.info(f"Игры по запросу '{query}' не найдены")
                return False, "Игры не найдены.", []

            result = []
            for game in games:
                price = game['price']
                discount = game['discount'] or 0
                final_price = price * (1.0 - discount / 100.0)
                game_text = (
                    f"*ID*: {game['id']}\n"
                    f"*Игра*: {game['game_name']}\n"
                    f"*Цена*: ${final_price:.2f}\n"
                    f"*Скидка*: {discount}%\n"
                    f"*Жанр*: {game['genre'] or 'Не указан'}\n"
                    f"*Регион*: {game['region'] or 'Не указан'}"
                )
                result.append({
                    'text': game_text,
                    'image_urls': game['image_urls'] or ''
                })
            logger.info(f"Найдено {len(games)} игр по запросу '{query}'")
            return True, "Игры найдены.", result
    except Exception as e:
        logger.error(f"Ошибка поиска игр: {e}", exc_info=True)
        return False, f"Ошибка поиска игр: {str(e)}", []

async def create_order(user_id, game_id):
    """Создаёт заказ для пользователя."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            # Проверяем, существует ли пользователь в таблице users
            cursor = await db.execute('SELECT * FROM users WHERE tg_id = ?', (user_id,))
            user = await cursor.fetchone()
            if not user:
                await db.execute('INSERT OR IGNORE INTO users (tg_id) VALUES (?)', (user_id,))
                await db.commit()
                logger.info(f"Добавлен новый пользователь с tg_id: {user_id}")

            cursor = await db.execute('SELECT * FROM steam_keys WHERE id = ? AND count > 0', (game_id,))
            game = await cursor.fetchone()
            if not game:
                logger.warning(f"Игра с ID {game_id} не найдена или недоступна")
                return False, "Игра не найдена или недоступна.", None

            cursor = await db.execute(
                'INSERT INTO orders (user_id, key_id, status, order_date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                (user_id, game_id, 'pending'))
            await db.commit()
            order_id = cursor.lastrowid
            order_data = {
                'order_id': order_id,
                'user_id': user_id,
                'game_name': game['game_name'],
                'key': game['st_key']
            }
            logger.info(f"Создан заказ #{order_id} для пользователя {user_id}, игра: {game['game_name']}")
            return True, "Заказ успешно создан.", order_data
    except Exception as e:
        logger.error(f"Ошибка создания заказа: {e}", exc_info=True)
        return False, f"Ошибка создания заказа: {str(e)}", None

async def confirm_order(order_id):
    """Подтверждает заказ и отправляет ключ пользователю."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM orders WHERE id = ? AND status = ?', (order_id, 'pending'))
            order = await cursor.fetchone()
            if not order:
                logger.warning(f"Заказ с ID {order_id} не найден или уже обработан")
                return False, "Заказ не найден или уже обработан.", None

            cursor = await db.execute('SELECT * FROM steam_keys WHERE id = ?', (order['key_id'],))
            game = await cursor.fetchone()
            if not game:
                logger.warning(f"Игра с ID {order['key_id']} не найдена")
                return False, "Игра не найдена.", None

            await db.execute('UPDATE orders SET status = ? WHERE id = ?', ('confirmed', order_id))
            await db.execute('UPDATE steam_keys SET count = count - 1 WHERE id = ?', (order['key_id'],))
            await db.commit()

            order_data = {
                'order_id': order_id,
                'user_id': order['user_id'],
                'game_name': game['game_name'],
                'key': game['st_key']
            }
            logger.info(f"Заказ #{order_id} подтверждён для пользователя {order['user_id']}")
            return True, "Заказ подтверждён.", order_data
    except Exception as e:
        logger.error(f"Ошибка подтверждения заказа: {e}", exc_info=True)
        return False, f"Ошибка подтверждения заказа: {str(e)}", None

async def cancel_order(order_id):
    """Отменяет заказ."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            cursor = await db.execute('SELECT * FROM orders WHERE id = ? AND status = ?', (order_id, 'pending'))
            order = await cursor.fetchone()
            if not order:
                logger.warning(f"Заказ с ID {order_id} не найден или уже обработан")
                return False, "Заказ не найден или уже обработан."

            await db.execute('UPDATE orders SET status = ? WHERE id = ?', ('cancelled', order_id))
            await db.commit()
            logger.info(f"Заказ #{order_id} отменён")
            return True, "Заказ отменён."
    except Exception as e:
        logger.error(f"Ошибка отмены заказа: {e}", exc_info=True)
        return False, f"Ошибка отмены заказа: {str(e)}"

async def get_pending_orders():
    """Возвращает список ожидающих заказов."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                                      SELECT o.id AS order_id, o.user_id, o.key_id, o.status, o.order_date, s.game_name
                                      FROM orders o
                                               JOIN steam_keys s ON o.key_id = s.id
                                      WHERE o.status = ?
                                      ''', ('pending',))
            orders = await cursor.fetchall()
            if not orders:
                logger.info("Ожидающие заказы не найдены")
                return False, "Ожидающие заказы не найдены.", []

            result = []
            for order in orders:
                result.append({
                    'order_id': order['order_id'],
                    'user_id': order['user_id'],
                    'game_name': order['game_name'],
                    'order_date': order['order_date']
                })
            logger.info(f"Найдено {len(orders)} ожидающих заказов")
            return True, "Ожидающие заказы найдены.", result
    except Exception as e:
        logger.error(f"Ошибка получения заказов: {e}", exc_info=True)
        return False, f"Ошибка получения заказов: {str(e)}", []

async def get_analytics():
    """Возвращает аналитику продаж."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                                      SELECT COUNT(*) as total_orders, SUM(s.price * (1.0 - s.discount / 100.0)) as total_revenue
                                      FROM orders o
                                               JOIN steam_keys s ON o.key_id = s.id
                                      WHERE o.status = ?
                                      ''', ('confirmed',))
            stats = await cursor.fetchone()
            if not stats:
                logger.info("Аналитика недоступна: нет подтверждённых заказов")
                return False, "Аналитика недоступна.", []

            data = [
                f"Всего заказов: {stats['total_orders']}",
                f"Общая выручка: ${stats['total_revenue'] or 0:.2f}"
            ]
            logger.info(f"Аналитика: {data}")
            return True, "Аналитика продаж:", data
    except Exception as e:
        logger.error(f"Ошибка получения аналитики: {e}", exc_info=True)
        return False, f"Ошибка получения аналитики: {str(e)}", []