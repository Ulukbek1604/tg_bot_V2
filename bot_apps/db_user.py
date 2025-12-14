# bot_apps/db_user.py
import aiosqlite
import html
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


async def _apply_sale_to_game(game) -> dict:
    """Работает и с sqlite3.Row, и с dict — без ошибок"""
    from datetime import datetime
    import re

    # Превращаем sqlite3.Row в обычный dict — теперь .get() работает
    g = dict(game)

    price = float(g.get('price', 0))
    discount = int(g.get('discount', 0))

    sale_active = bool(g.get('sale_active', 0))
    sale_not = (g.get('sale_not') or "").strip()
    sale_ends_at = g.get('sale_ends_at')

    final_price = price
    sale_text = ""

    # Обычная скидка (поле discount)
    if discount > 0 and not sale_active:
        final_price = price * (1 - discount / 100)
        sale_text = f"Скидка {discount}%"

    # Новая акция
    if sale_active and sale_not:
        now = datetime.now()
        expired = False

        if sale_ends_at:
            try:
                if len(sale_ends_at) <= 10:
                    end_dt = datetime.strptime(sale_ends_at, "%Y-%m-%d")
                else:
                    end_dt = datetime.strptime(sale_ends_at[:19], "%Y-%m-%d %H:%M:%S")
                if now > end_dt:
                    expired = True
            except:
                pass

        if expired:
            async with aiosqlite.connect('tg_bot.db') as db:
                await db.execute(
                    "UPDATE steam_keys SET sale_active = 0, sale_not = NULL, sale_ends_at = NULL WHERE id = ?",
                    (g['id'],)
                )
                await db.commit()
            sale_active = False
        else:
            match = re.search(r'(\d+)%', sale_not, re.IGNORECASE)
            if match:
                percent = int(match.group(1))
                final_price = price * (1 - percent / 100)
                end_date = sale_ends_at.split()[0] if sale_ends_at else "скоро"
                sale_text = f"АКЦИЯ! {sale_not} до {end_date}"
            else:
                sale_text = f"АКЦИЯ! {sale_not}"

    return {
        "final_price": round(final_price, 2),
        "sale_text": sale_text
    }


async def show_all_games():
    """Показать весь каталог"""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM steam_keys WHERE count > 0 ORDER BY id')
            games = await cursor.fetchall()
            games = [dict(row) for row in games]
            if not games:
                return False, "Игры не найдены.", []

            result = []
            for game in games:
                sale = await _apply_sale_to_game(game)
                text = (
                    f"*ID*: {game['id']}\n"
                    f"*Игра*: {game['game_name']}\n"
                    f"*Цена*: ${sale['final_price']:.2f}"
                )
                if sale['sale_text']:
                    text += f"\n{sale['sale_text']}"
                if game.get('genre'):
                    text += f"\n*Жанр*: {game['genre']}"
                if game.get('region'):
                    text += f"\n*Регион*: {game['region'] or 'Глобальный'}"

                result.append({
                    'text': text,
                    'image_urls': game.get('image_urls') or ''
                })

            return True, "Доступные игры:", result

    except Exception as e:
        logger.error(f"Ошибка в show_all_games: {e}", exc_info=True)
        return False, f"Ошибка: {str(e)}", []


async def search_games(query):
    """Поиск по названию или ID"""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row

            if query.strip().isdigit():
                game_id = int(query.strip())
                cursor = await db.execute('SELECT * FROM steam_keys WHERE id = ? AND count > 0', (game_id,))
            else:
                cursor = await db.execute(
                    'SELECT * FROM steam_keys WHERE game_name LIKE ? AND count > 0',
                    (f'%{query.strip()}%',)
                )

            games = await cursor.fetchall()
            games = [dict(row) for row in games]
            if not games:
                return False, "Игры не найдены.", []

            result = []
            for game in games:
                sale = await _apply_sale_to_game(game)
                text = (
                    f"*ID*: {game['id']}\n"
                    f"*Игра*: {game['game_name']}\n"
                    f"*Цена*: ${sale['final_price']:.2f}"
                )
                if sale['sale_text']:
                    text += f"\n{sale['sale_text']}"
                if game.get('genre'):
                    text += f"\n*Жанр*: {game['genre']}"
                if game.get('region'):
                    text += f"\n*Регион*: {game['region'] or 'Глобальный'}"

                result.append({
                    'text': text,
                    'image_urls': game.get('image_urls') or ''
                })

            return True, "Результаты поиска:", result

    except Exception as e:
        logger.error(f"Ошибка в search_games: {e}", exc_info=True)
        return False, f"Ошибка поиска: {str(e)}", []


async def filter_games_by_price(price_limit):
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM steam_keys WHERE count > 0 AND price <= ?',
                (float(price_limit),)
            )
            games = await cursor.fetchall()
            games = [dict(row) for row in games]

            if not games:
                return False, f"Игры до ${price_limit} не найдены.", []

            result = []
            for game in games:
                sale = await _apply_sale_to_game(game)
                text = (
                    f"*ID*: {game['id']}\n"
                    f"*Игра*: {game['game_name']}\n"
                    f"*Цена*: ${sale['final_price']:.2f}"
                )
                if sale['sale_text']:
                    text += f"\n{sale['sale_text']}"

                result.append({
                    'text': text,
                    'image_urls': game.get('image_urls') or ''
                })

            return True, f"Игры до ${price_limit}:", result

    except Exception as e:
        logger.error(f"Ошибка в filter_games_by_price: {e}", exc_info=True)
        return False, f"Ошибка: {str(e)}", []


async def filter_games_by_genre(genre):
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                'SELECT * FROM steam_keys WHERE count > 0 AND genre LIKE ?',
                (f'%{genre}%',)
            )
            games = await cursor.fetchall()
            games = [dict(row) for row in games]

            if not games:
                return False, f"Игры жанра '{genre}' не найдены.", []

            result = []
            for game in games:
                sale = await _apply_sale_to_game(game)
                text = (
                    f"*ID*: {game['id']}\n"
                    f"*Игра*: {game['game_name']}\n"
                    f"*Цена*: ${sale['final_price']:.2f}"
                )
                if sale['sale_text']:
                    text += f"\n{sale['sale_text']}"

                result.append({
                    'text': text,
                    'image_urls': game.get('image_urls') or ''
                })

            return True, f"Игры жанра '{genre}':", result

    except Exception as e:
        logger.error(f"Ошибка в filter_games_by_genre: {e}", exc_info=True)
        return False, f"Ошибка: {str(e)}", []



async def search_games(query):
    """Поиск игр по названию или по ID."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row

            # Попробуем определить, является ли query числом (ID)
            query_clean = query.strip()
            if re.fullmatch(r'\d+', query_clean):  # Только цифры → это ID
                game_id = int(query_clean)
                cursor = await db.execute(
                    'SELECT * FROM steam_keys WHERE id = ? AND count > 0',
                    (game_id,)
                )
                logger.info(f"Поиск игры по ID: {game_id}")
            else:
                # Поиск по названию (частичное совпадение)
                cursor = await db.execute(
                    'SELECT * FROM steam_keys WHERE game_name LIKE ? AND count > 0',
                    (f'%{query_clean}%',)
                )
                logger.info(f"Поиск игр по названию: '{query_clean}'")

            games = await cursor.fetchall()
            games = [dict(row) for row in games]

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

    except ValueError as e:
        logger.error(f"Ошибка преобразования ID: {e}", exc_info=True)
        return False, "Некорректный ID игры.", []
    except Exception as e:
        logger.error(f"Ошибка поиска игр: {e}", exc_info=True)
        return False, f"Ошибка поиска: {str(e)}", []

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

async def get_pending_orders(games=None):
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
            games = [dict(row) for row in games]
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