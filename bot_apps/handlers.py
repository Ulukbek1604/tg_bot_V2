import html
import shlex
import logging
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot_apps import keyboards as kb
from bot_apps import db_user
from bot_apps import db_admin
import aiosqlite

logging.basicConfig(level=logging.INFO, filename='bot.log')
logger = logging.getLogger(__name__)

rt = Router()

# Реквизиты для оплаты
PAYMENT_DETAILS = (
    "📩 Пожалуйста, переведите оплату по следующим реквизитам:\n"
    "💳 Номер М банка: 223991488\n"
    "👤 Имя держателя: Турдумаматов Улукбек\n"
)


async def get_admin_ids():
    """Получает список ID администраторов из базы данных."""
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT tg_id FROM admins')
            admins = await cursor.fetchall()
            return [admin['tg_id'] for admin in admins]
    except Exception as e:
        logger.error(f"Ошибка при получении списка администраторов: {e}", exc_info=True)
        return []


@rt.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    """Обработчик кнопки 'Админ панель'."""
    logger.info(f"Нажата кнопка 'Админ-панель' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        await callback.message.edit_text(
            html.escape("Админ-панель: выберите действие"),
            reply_markup=kb.get_admin_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug(f"Сообщение не изменено, пропускаем: {e}")
        else:
            logger.error(f"Ошибка в обработчике admin_panel: {e}", exc_info=True)
            await callback.answer("Произошла ошибка.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_panel: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data == "admin_add_product")
async def admin_add_product_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Добавить продукт'."""
    logger.info(f"Нажата кнопка 'Добавить продукт' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        await callback.message.answer(
            html.escape(
                "Формат: /add_product 'название игры' 'цена' 'количество' 'жанр' 'страна' 'ключ' ['URL1,URL2,URL3']"),
            parse_mode='HTML'
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_add_product: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data == "admin_edit_product")
async def admin_edit_product_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Редактировать продукт'."""
    logger.info(f"Нажата кнопка 'Редактировать продукт' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        await callback.message.answer(
            html.escape(
                "Формат: /edit_product 'ID' ['название'] ['цена'] ['скидка'] ['жанр'] ['страна'] ['URL1,URL2,URL3']"),
            parse_mode='HTML'
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_edit_product: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data == "admin_delete_product")
async def admin_delete_product_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Удалить продукт'."""
    logger.info(f"Нажата кнопка 'Удалить продукт' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        await callback.message.answer(
            html.escape("Формат: /delete_product 'ID'"),
            parse_mode='HTML'
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_delete_product: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data == "admin_set_discount")
async def admin_set_discount_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Установить скидку'."""
    logger.info(f"Нажата кнопка 'Установить скидку' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        await callback.message.answer(
            html.escape("Формат: /set_discount 'ID' 'скидка'"),
            parse_mode='HTML'
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_set_discount: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data == "admin_orders")
async def admin_orders_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Заказы'."""
    logger.info(f"Нажата кнопка 'Заказы' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        success, msg, orders = await db_user.get_pending_orders()
        if success and orders:
            for order in orders:
                await callback.message.answer(
                    html.escape(
                        f"*Заказ ID*: {order['order_id']}\n"
                        f"*Пользователь*: {order['user_id']}\n"
                        f"*Игра*: {order['game_name']}\n"
                        f"*Дата*: {order['order_date']}"
                    ),
                    reply_markup=kb.get_order_actions_keyboard(order['order_id']),
                    parse_mode='HTML'
                )
        else:
            await callback.message.answer(
                html.escape(msg),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_orders: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data == "admin_manage_users")
async def admin_manage_users_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Управление админами'."""
    logger.info(f"Нажата кнопка 'Управление админами' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        success, msg, admins = await db_admin.get_admins()
        if success and admins:
            await callback.message.answer(
                html.escape(msg + "\n\n" + "\n\n".join(admins)),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        else:
            await callback.message.answer(
                html.escape(msg),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_manage_users: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data == "admin_analytics")
async def admin_analytics_callback(callback: CallbackQuery):
    """Обработчик кнопки 'Аналитика'."""
    logger.info(f"Нажата кнопка 'Аналитика' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        success, msg, data = await db_user.get_analytics()
        if success and data:
            await callback.message.answer(
                html.escape(msg + "\n\n" + "\n".join(data)),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        else:
            await callback.message.answer(
                html.escape(msg),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_analytics: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.message(Command('buy'))
async def buy(message: Message, bot: Bot):
    """Обработчик команды /buy."""
    logger.info(f"Команда /buy от пользователя {message.from_user.id}")
    try:
        args = shlex.split(message.text)[1:]
        if not args:
            await message.answer(
                html.escape("Формат: /buy 'ID игры'"),
                parse_mode='HTML'
            )
            return
        game_id = int(args[0])
        success, msg, order_data = await db_user.create_order(message.from_user.id, game_id)
        if success and order_data:
            await message.answer(
                html.escape(
                    f"Заказ #{order_data['order_id']} на '{order_data['game_name']}' создан!\n{PAYMENT_DETAILS}"),
                parse_mode='HTML'
            )
            admin_ids = await get_admin_ids()
            for admin_id in admin_ids:
                await bot.send_message(
                    admin_id,
                    html.escape(
                        f"Новый заказ #{order_data['order_id']}!\nПользователь: @{message.from_user.username or message.from_user.id}\nИгра: {order_data['game_name']}"),
                    reply_markup=kb.get_order_actions_keyboard(order_data['order_id']),
                    parse_mode='HTML'
                )
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("ID должен быть числом"),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /buy: {e}", exc_info=True)
        await message.answer("Произошла ошибка при покупке.")


@rt.callback_query(F.data.startswith("buy_"))
async def buy_callback(callback: CallbackQuery, bot: Bot):
    """Обработчик покупки через callback."""
    logger.info(f"Покупка {callback.data} от пользователя {callback.from_user.id}")
    try:
        game_id = int(callback.data.replace("buy_", ""))
        success, msg, order_data = await db_user.create_order(callback.from_user.id, game_id)
        if success and order_data:
            await callback.message.answer(
                html.escape(
                    f"Заказ #{order_data['order_id']} на '{order_data['game_name']}' создан!\n{PAYMENT_DETAILS}"),
                parse_mode='HTML'
            )
            admin_ids = await get_admin_ids()
            for admin_id in admin_ids:
                await bot.send_message(
                    admin_id,
                    html.escape(
                        f"Новый заказ #{order_data['order_id']}!\nПользователь: @{callback.from_user.username or callback.from_user.id}\nИгра: {order_data['game_name']}"),
                    reply_markup=kb.get_order_actions_keyboard(order_data['order_id']),
                    parse_mode='HTML'
                )
        await callback.message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
        await callback.answer()
    except ValueError:
        await callback.message.answer(
            html.escape("Неверный ID игры"),
            parse_mode='HTML'
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике покупки: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при покупке.", show_alert=True)


@rt.callback_query(F.data.startswith("confirm_order_"))
async def confirm_order_callback(callback: CallbackQuery, bot: Bot):
    """Обработчик подтверждения заказа."""
    logger.info(f"Подтверждение заказа {callback.data} от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        order_id = int(callback.data.replace("confirm_order_", ""))
        success, msg, order_data = await db_user.confirm_order(order_id)
        if success and order_data:
            await bot.send_message(
                order_data['user_id'],
                html.escape(
                    f"Ваш заказ #{order_data['order_id']} подтверждён!\nИгра: {order_data['game_name']}\nКлюч: {order_data['key']}"),
                parse_mode='HTML'
            )
            await callback.message.edit_text(
                html.escape(f"Заказ #{order_id} подтверждён. Ключ отправлен пользователю."),
                parse_mode='HTML'
            )
        else:
            await callback.message.answer(
                html.escape(msg),
                parse_mode='HTML'
            )
        await callback.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug(f"Сообщение не изменено, пропускаем: {e}")
        else:
            logger.error(f"Ошибка в обработчике подтверждения заказа: {e}", exc_info=True)
            await callback.answer("Произошла ошибка.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в обработчике подтверждения заказа: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order_callback(callback: CallbackQuery):
    """Обработчик отмены заказа."""
    logger.info(f"Отмена заказа {callback.data} от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return
        order_id = int(callback.data.replace("cancel_order_", ""))
        success, msg = await db_user.cancel_order(order_id)
        await callback.message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
        await callback.answer()
    except ValueError:
        await callback.message.answer(
            html.escape("Неверный ID заказа"),
            parse_mode='HTML'
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике отмены заказа: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.message(Command('pending_orders'))
async def pending_orders(message: Message):
    """Обработчик команды /pending_orders для админов."""
    logger.info(f"Команда /pending_orders от пользователя {message.from_user.id}")
    try:
        if not await db_admin.is_admin(message.from_user.id):
            await message.answer(
                html.escape("Эта команда доступна только администратору."),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
            return
        success, msg, orders = await db_user.get_pending_orders()
        if success and orders:
            for order in orders:
                await message.answer(
                    html.escape(
                        f"*Заказ ID*: {order['order_id']}\n"
                        f"*Пользователь*: {order['user_id']}\n"
                        f"*Игра*: {order['game_name']}\n"
                        f"*Дата*: {order['order_date']}"
                    ),
                    reply_markup=kb.get_order_actions_keyboard(order['order_id']),
                    parse_mode='HTML'
                )
        else:
            await message.answer(
                html.escape(msg),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /pending_orders: {e}", exc_info=True)
        await message.answer("Произошла ошибка при получении заказов.")


@rt.message(F.photo)
async def handle_payment_screenshot(message: Message, bot: Bot):
    """Обработчик скриншотов оплаты от пользователей."""
    logger.info(f"Получен скриншот оплаты от пользователя {message.from_user.id}")
    try:
        admin_ids = await get_admin_ids()
        for admin_id in admin_ids:
            await bot.send_photo(
                admin_id,
                photo=message.photo[-1].file_id,
                caption=html.escape(
                    f"Скриншот оплаты от пользователя @{message.from_user.username or message.from_user.id}")
            )
        await message.answer(
            html.escape("Скриншот отправлен администратору. Ожидайте подтверждения."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике скриншотов: {e}", exc_info=True)
        await message.answer("Произошла ошибка при отправке скриншота.")


@rt.message(Command('add_product'))
async def add_product(message: Message):
    """Обработчик команды /add_product."""
    logger.info(f"Команда /add_product от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администратору."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]
        if len(args) < 6:
            await message.answer(
                html.escape(
                    "Формат: /add_product 'название игры' 'цена' 'количество' 'жанр' 'страна' 'ключ' ['URL1,URL2,URL3']"),
                parse_mode='HTML'
            )
            return
        game_name, price, count, genre, region, st_key = args[:6]
        image_urls = args[6] if len(args) > 6 else None
        price = int(price)
        count = int(count)
        if price < 0:
            await message.answer(
                html.escape("Цена не может быть отрицательной"),
                parse_mode='HTML'
            )
            return
        if count < 1:
            await message.answer(
                html.escape("Количество ключей должно быть больше 0"),
                parse_mode='HTML'
            )
            return
        success, msg = await db_user.add_steam_key_into_db(game_name, st_key, price, count, genre, region, image_urls)
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("Цена и количество должны быть числами"),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /add_product: {e}", exc_info=True)
        await message.answer("Произошла ошибка при добавлении продукта.")


@rt.message(Command('edit_product'))
async def edit_product(message: Message):
    """Обработчик команды /edit_product."""
    logger.info(f"Команда /edit_product от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администратору."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]
        if len(args) < 1:
            await message.answer(
                html.escape(
                    "Формат: /edit_product 'ID' ['название'] ['цена'] ['скидка'] ['жанр'] ['страна'] ['URL1,URL2,URL3']"),
                parse_mode='HTML'
            )
            return
        game_id = int(args[0])
        # Передаём только указанные параметры, пустые строки или None игнорируются
        game_name = args[1] if len(args) > 1 and args[1] else None
        price = int(args[2]) if len(args) > 2 and args[2] else None
        discount = int(args[3]) if len(args) > 3 and args[3] else None
        genre = args[4] if len(args) > 4 and args[4] else None
        region = args[5] if len(args) > 5 and args[5] else None
        image_urls = args[6] if len(args) > 6 and args[6] else None
        success, msg = await db_user.edit_steam_key_into_db(
            game_id, game_name=game_name, price=price, discount=discount,
            genre=genre, region=region, image_urls=image_urls
        )
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("ID, цена и скидка должны быть числами"),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /edit_product: {e}", exc_info=True)
        await message.answer("Произошла ошибка при редактировании продукта.")


@rt.message(Command('delete_product'))
async def delete_product(message: Message):
    """Обработчик команды /delete_product."""
    logger.info(f"Команда /delete_product от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администратору."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]
        if not args:
            await message.answer(
                html.escape("Формат: /delete_product 'ID'"),
                parse_mode='HTML'
            )
            return
        game_id = int(args[0])
        success, msg = await db_user.delete_steam_key_from_db(game_id)
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("ID должен быть числом"),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /delete_product: {e}", exc_info=True)
        await message.answer("Произошла ошибка при удалении продукта.")


@rt.message(Command('set_discount'))
async def set_discount(message: Message):
    """Обработчик команды /set_discount."""
    logger.info(f"Команда /set_discount от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администратору."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]
        if len(args) != 2:
            await message.answer(
                html.escape("Формат: /set_discount 'ID' 'скидка'"),
                parse_mode='HTML'
            )
            return
        game_id, discount = map(int, args)
        if not (0 <= discount <= 100):
            await message.answer(
                html.escape("Скидка должна быть от 0 до 100%"),
                parse_mode='HTML'
            )
            return
        success, msg = await db_user.edit_steam_key_into_db(game_id, discount=discount)
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("ID и скидка должны быть числами"),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /set_discount: {e}", exc_info=True)
        await message.answer("Произошла ошибка при установке скидки.")


@rt.message(Command('orders'))
async def orders(message: Message):
    """Обработчик команды /orders."""
    logger.info(f"Команда /orders от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администратору."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        success, msg, orders = await db_user.get_pending_orders()
        if success and orders:
            for order in orders:
                await message.answer(
                    html.escape(
                        f"*Заказ ID*: {order['order_id']}\n"
                        f"*Пользователь*: {order['user_id']}\n"
                        f"*Игра*: {order['game_name']}\n"
                        f"*Дата*: {order['order_date']}"
                    ),
                    reply_markup=kb.get_order_actions_keyboard(order['order_id']),
                    parse_mode='HTML'
                )
        else:
            await message.answer(
                html.escape(msg),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /orders: {e}", exc_info=True)
        await message.answer("Произошла ошибка при получении заказов.")


@rt.message(Command('manage_users'))
async def manage_users(message: Message):
    """Обработчик команды /manage_users."""
    logger.info(f"Команда /manage_users от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администратору."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        success, msg, admins = await db_admin.get_admins()
        if success and admins:
            await message.answer(
                html.escape(msg + "\n\n" + "\n\n".join(admins)),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                html.escape(msg),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /manage_users: {e}", exc_info=True)
        await message.answer("Произошла ошибка при управлении пользователями.")


@rt.message(Command('add_admin'))
async def add_admin(message: Message):
    """Обработчик команды /add_admin."""
    logger.info(f"Команда /add_admin от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администратору."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]
        if len(args) != 2:
            await message.answer(
                html.escape("Формат: /add_admin 'tg_id' 'имя'"),
                parse_mode='HTML'
            )
            return
        tg_id = int(args[0])
        name = args[1]
        success, msg = await db_admin.add_admin(tg_id, name)
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("ID должен быть числом"),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /add_admin: {e}", exc_info=True)
        await message.answer("Произошла ошибка при добавлении админа.")


@rt.message(Command('remove_admin'))
async def remove_admin(message: Message):
    """Обработчик команды /remove_admin."""
    logger.info(f"Команда /remove_admin от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администратору."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]
        if not args:
            await message.answer(
                html.escape("Формат: /remove_admin 'ID'"),
                parse_mode='HTML'
            )
            return
        tg_id = int(args[0])
        success, msg = await db_admin.remove_admin(tg_id)
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("ID должен быть числом"),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /remove_admin: {e}", exc_info=True)
        await message.answer("Произошла ошибка при удалении админа.")


@rt.message(Command('analytics'))
async def analytics(message: Message):
    """Обработчик команды /analytics."""
    logger.info(f"Команда /analytics от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администратору."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        success, msg, data = await db_user.get_analytics()
        if success and data:
            await message.answer(
                html.escape(msg + "\n\n" + "\n".join(data)),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                html.escape(msg),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /analytics: {e}", exc_info=True)
        await message.answer("Произошла ошибка при получении аналитики.")


@rt.message(CommandStart())
async def start(message: Message):
    """Обработчик команды /start."""
    logger.info(f"Команда /start от пользователя {message.from_user.id}")
    try:
        is_admin = await db_admin.is_admin(message.from_user.id) # Проверка на админа
        main_menu = kb.get_main_menu() # Получение клавиатуры главной меню
        admin_menu = kb.get_admin_main_menu(is_admin)
        await message.reply(
            html.escape(
                f"Привет, {message.from_user.full_name}! Это бот для покупки Steam ключей (ID: {message.from_user.id})"),
            reply_markup=main_menu,
            parse_mode='HTML'
        )
        if admin_menu: # Вывод админ меню если пользователь админ
            await message.answer(
                "Админ-меню доступно:",
                reply_markup=admin_menu
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {e}", exc_info=True)
        await message.reply("Произошла ошибка. Попробуйте позже.")


@rt.message(F.text == 'Каталог')
async def catalog(message: Message):
    """Обработчик кнопки 'Каталог'."""
    logger.info(f"Нажата кнопка 'Каталог' от пользователя {message.from_user.id}")
    try:
        await message.answer(
            html.escape("Выберите способ отображения каталога:"),
            reply_markup=kb.get_catalog_choice_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в обработчике каталога: {e}", exc_info=True)
        await message.answer("Произошла ошибка при загрузке каталога.")


@rt.callback_query(F.data == "show_all_games")
async def show_all_games_callback(callback: CallbackQuery):
    """Обработчик выбора 'Весь список' в каталоге."""
    logger.info(f"Нажата кнопка 'Весь список' от пользователя {callback.from_user.id}")
    try:
        success, msg, games = await db_user.show_all_games()
        logger.debug(f"Результат catalog: success={success}, msg={msg}, games_count={len(games)}")
        if success and games:
            for game in games:
                game_id = int(game['text'].split("\n")[0].replace("*ID*: ", ""))
                image_urls = game['image_urls'].split(',') if game['image_urls'] else []
                if image_urls:
                    for image_url in image_urls:
                        if image_url.strip():
                            try:
                                await callback.message.answer_photo(
                                    photo=image_url.strip(),
                                    caption=html.escape(game['text']) if image_url == image_urls[0] else None,
                                    reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game") if image_url ==
                                                                                                            image_urls[
                                                                                                                0] else None,
                                    parse_mode='HTML'
                                )
                            except TelegramBadRequest as e:
                                logger.error(f"Ошибка отправки изображения {image_url}: {e}")
                                await callback.message.answer(
                                    html.escape(game['text']),
                                    reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                                    parse_mode='HTML'
                                )
                        else:
                            await callback.message.answer(
                                html.escape(game['text']),
                                reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                                parse_mode='HTML'
                            )
                else:
                    await callback.message.answer(
                        html.escape(game['text']),
                        reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                        parse_mode='HTML'
                    )
            await callback.message.answer(
                "Каталог игр:",
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        else:
            await callback.message.answer(
                html.escape(f"{msg} Пожалуйста, добавьте игры с помощью команды /add_product"),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике show_all_games: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при загрузке каталога.", show_alert=True)


@rt.callback_query(F.data == "show_filters")
async def show_filters_callback(callback: CallbackQuery):
    """Обработчик выбора 'По фильтру' в каталоге."""
    logger.info(f"Нажата кнопка 'По фильтру' от пользователя {callback.from_user.id}")
    try:
        await callback.message.edit_text(
            html.escape("Выберите тип фильтра:"),
            reply_markup=kb.get_filter_type_keyboard(),
            parse_mode='HTML'
        )
        await callback.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug(f"Сообщение не изменено, пропускаем: {e}")
        else:
            logger.error(f"Ошибка в обработчике show_filters: {e}", exc_info=True)
            await callback.answer("Произошла ошибка.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в обработчике show_filters: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data == "filter_by_price")
async def filter_by_price_callback(callback: CallbackQuery):
    """Обработчик выбора фильтра по цене."""
    logger.info(f"Нажата кнопка 'Фильтр по цене' от пользователя {callback.from_user.id}")
    try:
        await callback.message.edit_text(
            html.escape("Выберите ценовой диапазон:"),
            reply_markup=kb.get_price_filter_keyboard(),
            parse_mode='HTML'
        )
        await callback.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug(f"Сообщение не изменено, пропускаем: {e}")
        else:
            logger.error(f"Ошибка в обработчике filter_by_price: {e}", exc_info=True)
            await callback.answer("Произошла ошибка.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в обработчике filter_by_price: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data == "filter_by_genre")
async def filter_by_genre_callback(callback: CallbackQuery):
    """Обработчик выбора фильтра по жанру."""
    logger.info(f"Нажата кнопка 'Фильтр по жанру' от пользователя {callback.from_user.id}")
    try:
        await callback.message.edit_text(
            html.escape("Выберите жанр:"),
            reply_markup=kb.get_genre_filter_keyboard(),
            parse_mode='HTML'
        )
        await callback.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug(f"Сообщение не изменено, пропускаем: {e}")
        else:
            logger.error(f"Ошибка в обработчике filter_by_genre: {e}", exc_info=True)
            await callback.answer("Произошла ошибка.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в обработчике filter_by_genre: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


@rt.callback_query(F.data.startswith("filter_price_"))
async def filter_price_callback(callback: CallbackQuery):
    """Обработчик фильтров по цене."""
    logger.info(f"Нажата кнопка фильтра {callback.data} от пользователя {callback.from_user.id}")
    try:
        price_limit = callback.data.replace("filter_price_", "")
        if price_limit == "none":
            success, msg, games = await db_user.show_all_games()
        else:
            price_limit = int(price_limit)
            success, msg, games = await db_user.filter_games_by_price(price_limit)

        logger.debug(f"Результат фильтра: success={success}, msg={msg}, games_count={len(games)}")
        if success and games:
            for game in games:
                game_id = int(game['text'].split("\n")[0].replace("*ID*: ", ""))
                image_urls = game['image_urls'].split(',') if game['image_urls'] else []
                if image_urls:
                    for image_url in image_urls:
                        if image_url.strip():
                            try:
                                await callback.message.answer_photo(
                                    photo=image_url.strip(),
                                    caption=html.escape(game['text']) if image_url == image_urls[0] else None,
                                    reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game") if image_url ==
                                                                                                            image_urls[
                                                                                                                0] else None,
                                    parse_mode='HTML'
                                )
                            except TelegramBadRequest as e:
                                logger.error(f"Ошибка отправки изображения {image_url}: {e}")
                                await callback.message.answer(
                                    html.escape(game['text']),
                                    reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                                    parse_mode='HTML'
                                )
                        else:
                            await callback.message.answer(
                                html.escape(game['text']),
                                reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                                parse_mode='HTML'
                            )
                else:
                    await callback.message.answer(
                        html.escape(game['text']),
                        reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                        parse_mode='HTML'
                    )
            await callback.message.answer(
                f"Игры с ценой до ${price_limit if price_limit != 'none' else 'без ограничений'}:",
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        else:
            await callback.message.answer(
                html.escape(f"{msg} Попробуйте изменить фильтр или добавить игры с помощью /add_product"),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике filter_price: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при применении фильтра.", show_alert=True)


@rt.callback_query(F.data.startswith("filter_genre_"))
async def filter_genre_callback(callback: CallbackQuery):
    """Обработчик фильтров по жанру."""
    logger.info(f"Нажата кнопка фильтра {callback.data} от пользователя {callback.from_user.id}")
    try:
        genre = callback.data.replace("filter_genre_", "")
        success, msg, games = await db_user.filter_games_by_genre(genre)

        logger.debug(f"Результат фильтра: success={success}, msg={msg}, games_count={len(games)}")
        if success and games:
            for game in games:
                game_id = int(game['text'].split("\n")[0].replace("*ID*: ", ""))
                image_urls = game['image_urls'].split(',') if game['image_urls'] else []
                if image_urls:
                    for image_url in image_urls:
                        if image_url.strip():
                            try:
                                await callback.message.answer_photo(
                                    photo=image_url.strip(),
                                    caption=html.escape(game['text']) if image_url == image_urls[0] else None,
                                    reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game") if image_url ==
                                                                                                            image_urls[
                                                                                                                0] else None,
                                    parse_mode='HTML'
                                )
                            except TelegramBadRequest as e:
                                logger.error(f"Ошибка отправки изображения {image_url}: {e}")
                                await callback.message.answer(
                                    html.escape(game['text']),
                                    reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                                    parse_mode='HTML'
                                )
                        else:
                            await callback.message.answer(
                                html.escape(game['text']),
                                reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                                parse_mode='HTML'
                            )
                else:
                    await callback.message.answer(
                        html.escape(game['text']),
                        reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                        parse_mode='HTML'
                    )
            await callback.message.answer(
                f"Игры жанра '{genre}':",
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        else:
            await callback.message.answer(
                html.escape(f"{msg} Попробуйте изменить фильтр или добавить игры с помощью /add_product"),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в обработчике filter_genre: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при применении фильтра.", show_alert=True)


@rt.message(F.text == 'Поиск')
async def search_button(message: Message):
    """Обработчик кнопки 'Поиск'."""
    logger.info(f"Нажата кнопка 'Поиск' от пользователя {message.from_user.id}")
    await message.answer(
        "Введите название игры для поиска:",
        reply_markup=kb.get_main_menu()
    )


@rt.message(Command('search'))
async def search(message: Message):
    """Обработчик команды /search."""
    logger.info(f"Команда /search от пользователя {message.from_user.id}")
    await message.answer(
        "Введите название игры для поиска:",
        reply_markup=kb.get_main_menu()
    )


@rt.message(F.text == 'Поддержка')
async def support_button(message: Message):
    """Обработчик кнопки 'Поддержка'."""
    logger.info(f"Нажата кнопка 'Поддержка' от пользователя {message.from_user.id}")
    await message.answer(
        "Для связи с поддержкой напишите нам в @saintbakir или на email aisbeisfim@gmail.com",
        reply_markup=kb.get_main_menu()
    )


@rt.message(Command('support'))
async def support(message: Message):
    """Обработчик команды /support."""
    logger.info(f"Команда /support от пользователя {message.from_user.id}")
    await message.answer(
        "Для связи с поддержкой напишите нам в @saintbakir или на email aisbeisfim@gmail.com.",
        reply_markup=kb.get_main_menu()
    )


@rt.message(F.text)
async def search_query(message: Message):
    """Обработчик поисковых запросов по тексту."""
    query = message.text.strip()
    logger.info(f"Поиск по запросу '{query}' от пользователя {message.from_user.id}")
    if query in ['Каталог', 'Поиск', 'Поддержка']:
        logger.info(f"Сообщение '{query}' является командой меню, игнорируем")
        return
    try:
        success, msg, games = await db_user.search_games(query)
        logger.debug(f"Результат search_games: success={success}, msg={msg}, games_count={len(games)}")
        if success and games:
            for game in games:
                game_id = int(game['text'].split("\n")[0].replace("*ID*: ", ""))
                image_urls = game['image_urls'].split(',') if game['image_urls'] else []
                if image_urls:
                    for image_url in image_urls:
                        if image_url.strip():
                            try:
                                await message.answer_photo(
                                    photo=image_url.strip(),
                                    caption=html.escape(game['text']) if image_url == image_urls[0] else None,
                                    reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game") if image_url ==
                                                                                                            image_urls[
                                                                                                                0] else None,
                                    parse_mode='HTML'
                                )
                            except TelegramBadRequest as e:
                                logger.error(f"Ошибка отправки изображения {image_url}: {e}")
                                await message.answer(
                                    html.escape(game['text']),
                                    reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                                    parse_mode='HTML'
                                )
                        else:
                            await message.answer(
                                html.escape(game['text']),
                                reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                                parse_mode='HTML'
                            )
                else:
                    await message.answer(
                        html.escape(game['text']),
                        reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                        parse_mode='HTML'
                    )
            await message.answer(
                "Результаты поиска:",
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                html.escape(f"{msg} Попробуйте изменить запрос или добавить игры с помощью /add_product"),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике поиска: {e}", exc_info=True)
        await message.answer("Произошла ошибка при поиске.")