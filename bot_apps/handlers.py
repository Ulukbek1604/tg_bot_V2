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
from aiogram.filters.command import CommandObject
from aiogram import types

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
async def admin_analytics(callback: CallbackQuery):
    """
    Обработчик кнопки 'Аналитика' в админ-меню.
    Показывает краткую сводку + подменю аналитики.
    """
    logger.info(f"Нажата кнопка 'Аналитика' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return

        ok_global, text_global, _ = await db_admin.get_global_order_stats()
        if not ok_global:
            text_global = "Не удалось получить общую статистику."

        # можно через edit_text, чтобы заменить текст в том же сообщении
        await callback.message.edit_text(
            text_global + "\n\nВыберите тип аналитики:",
            reply_markup=kb.get_admin_analytics_menu(),
            parse_mode="HTML"
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
        # разбираем аргументы
        args = shlex.split(message.text)[1:]
        if not args:
            await message.answer(
                html.escape("Формат: /buy 'ID игры'"),
                parse_mode='HTML'
            )
            return

        try:
            game_id = int(args[0])
        except ValueError:
            await message.answer(
                html.escape("ID должен быть числом"),
                parse_mode='HTML'
            )
            return

        # создаём заказ
        success, msg, order_data = await db_user.create_order(message.from_user.id, game_id)

        # если не получилось — показываем ошибку и ВЫХОД
        if not success or not order_data:
            await message.answer(
                html.escape(msg),
                parse_mode='HTML'
            )
            return

        # если всё ок — отправляем реквизиты пользователю
        await message.answer(
            html.escape(
                f"Заказ #{order_data['order_id']} на '{order_data['game_name']}' создан!\n{PAYMENT_DETAILS}"
            ),
            parse_mode='HTML'
        )

        # уведомляем админов (если тут что-то упадёт — юзеру уже всё ок показали)
        try:
            admin_ids = await get_admin_ids()
            for admin_id in admin_ids:
                try:
                    await bot.send_message(
                        admin_id,
                        html.escape(
                            f"Новый заказ #{order_data['order_id']}!\n"
                            f"Пользователь: @{message.from_user.username or message.from_user.id}\n"
                            f"Игра: {order_data['game_name']}"
                        ),
                        reply_markup=kb.get_order_actions_keyboard(order_data['order_id']),
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений администраторам: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"Ошибка в обработчике /buy: {e}", exc_info=True)
        await message.answer("Произошла ошибка при покупке.")


@rt.callback_query(F.data.startswith("buy_"))
async def buy_callback(callback: CallbackQuery, bot: Bot):
    """Обработчик покупки через callback."""
    logger.info(f"Покупка {callback.data} от пользователя {callback.from_user.id}")
    try:
        # парсим ID игры
        try:
            game_id = int(callback.data.replace("buy_", ""))
        except ValueError:
            await callback.message.answer(
                html.escape("Неверный ID игры"),
                parse_mode='HTML'
            )
            await callback.answer()
            return

        # создаём заказ
        success, msg, order_data = await db_user.create_order(callback.from_user.id, game_id)

        # если ошибка — говорим и выходим
        if not success or not order_data:
            await callback.message.answer(
                html.escape(msg),
                parse_mode='HTML'
            )
            await callback.answer()
            return

        # если всё ок — отправляем реквизиты
        await callback.message.answer(
            html.escape(
                f"Заказ #{order_data['order_id']} на '{order_data['game_name']}' создан!\n{PAYMENT_DETAILS}"
            ),
            parse_mode='HTML'
        )

        # уведомляем админов отдельно
        try:
            admin_ids = await get_admin_ids()
            for admin_id in admin_ids:
                try:
                    await bot.send_message(
                        admin_id,
                        html.escape(
                            f"Новый заказ #{order_data['order_id']}!\n"
                            f"Пользователь: @{callback.from_user.username or callback.from_user.id}\n"
                            f"Игра: {order_data['game_name']}"
                        ),
                        reply_markup=kb.get_order_actions_keyboard(order_data['order_id']),
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений администраторам: {e}", exc_info=True)

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
    user_id = message.from_user.id
    logger.info(f"Получен скриншот оплаты от пользователя {user_id}")
    try:
        admin_ids = await get_admin_ids()
        if not admin_ids:
            logger.warning("Не найдено ни одного администратора для отправки скриншота.")
            await message.answer(
                html.escape(
                    "Скриншот получен, но администраторы пока не настроены.\n"
                    "Напишите, пожалуйста, в поддержку."
                ),
                reply_markup=kb.get_main_menu(),
                parse_mode="HTML"
            )
            return

        errors = 0
        for admin_id in admin_ids:
            try:
                await bot.send_photo(
                    admin_id,
                    photo=message.photo[-1].file_id,
                    caption=html.escape(
                        f"Скриншот оплаты от пользователя "
                        f"@{message.from_user.username or message.from_user.id}"
                    )
                )
            except Exception as e:
                errors += 1
                logger.error(
                    f"Ошибка отправки скриншота админу {admin_id}: {e}",
                    exc_info=True
                )

        # Пользователю не обязательно знать, что одному админу не ушло
        if errors == 0:
            text = "Скриншот отправлен администратору. Ожидайте подтверждения."
        else:
            text = (
                "Скриншот отправлен, но не всем администраторам удалось доставить.\n"
                "Ожидайте подтверждения."
            )

        await message.answer(
            html.escape(text),
            reply_markup=kb.get_main_menu(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка в обработчике скриншотов: {e}", exc_info=True)
        await message.answer(
            "Произошла ошибка при отправке скриншота.",
            reply_markup=kb.get_main_menu()
        )



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


@rt.message(Command("remove_admin"))
async def remove_admin(message: Message, command: CommandObject):
    """Обработчик команды /remove_admin <tg_id>"""
    user_id = message.from_user.id if message.from_user else None
    logger.info("Команда /remove_admin от пользователя %s, text=%r", user_id, message.text)

    # 1) Проверка прав
    try:
        if not user_id or not await db_admin.is_admin(user_id):
            await message.answer(
                html.escape("Эта команда доступна только администратору."),
                reply_markup=kb.get_main_menu(),
                parse_mode="HTML",
            )
            return
    except Exception as e:
        logger.exception("Ошибка при проверке прав администратора: %s", e)
        await message.answer("Не удалось проверить права администратора.")
        return

    # 2) Парсинг аргумента (без shlex)
    raw_args = (command.args or "").strip()  # всё, что после /remove_admin
    if not raw_args:
        await message.answer(html.escape("Формат: /remove_admin <ID>"), parse_mode="HTML")
        return

    # Удаляем обычные пробелы и невидимые символы по краям
    cleaned = "".join(ch for ch in raw_args if ch.isdigit())
    # Если были пробелы внутри (типа "709 789 903"), можно убрать их:
    if not cleaned:
        await message.answer(html.escape("ID должен быть числом"), parse_mode="HTML")
        return

    try:
        tg_id = int(cleaned)
    except Exception:
        await message.answer(html.escape("ID должен быть числом"), parse_mode="HTML")
        return

    # 3) Вызов БД с аккуратной обработкой ошибок
    try:
        result = await db_admin.remove_admin(tg_id)
        # допускаем, что функция может вернуть строку, булево, или кортеж
        if isinstance(result, tuple) and len(result) >= 2:
            success, msg = bool(result[0]), str(result[1])
        elif isinstance(result, bool):
            success, msg = result, ("Админ удалён" if result else "Админ не найден или не удалён")
        else:
            # что бы ни вернули — приведём к строке
            success, msg = True, str(result)

        await message.answer(html.escape(msg), parse_mode="HTML")
    except Exception as e:
        logger.exception("Ошибка в обработчике /remove_admin при удалении: %s", e)
        # Можно отдать человеку (только админу) короткую диагностику
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


# ---------- SUPPORT: замени старые хендлеры "Поддержка" и /support этим блоком ----------

# Инициализация таблицы tickets (вызови init_support_db() при старте в main.py)
async def init_support_db():
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    admin_id INTEGER,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await db.commit()
        logger.info("init_support_db: таблица tickets готова")
    except Exception as e:
        logger.exception(f"init_support_db error: {e}")

# Утилиты для работы с тикетами
async def create_ticket(user_id: int) -> int:
    async with aiosqlite.connect('tg_bot.db') as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("INSERT INTO tickets (user_id, status) VALUES (?, ?)", (user_id, "open"))
        await db.commit()
        return cur.lastrowid

async def set_ticket_admin(ticket_id: int, admin_id: int):
    async with aiosqlite.connect('tg_bot.db') as db:
        db.row_factory = aiosqlite.Row
        await db.execute("UPDATE tickets SET admin_id = ?, status = 'accepted' WHERE id = ?", (admin_id, ticket_id))
        await db.commit()

async def close_ticket(ticket_id: int):
    async with aiosqlite.connect('tg_bot.db') as db:
        db.row_factory = aiosqlite.Row
        await db.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (ticket_id,))
        await db.commit()

async def get_ticket(ticket_id: int):
    async with aiosqlite.connect('tg_bot.db') as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        return await cur.fetchone()

async def find_active_ticket_by_user(user_id: int):
    async with aiosqlite.connect('tg_bot.db') as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, admin_id FROM tickets WHERE user_id = ? AND status = 'accepted' ORDER BY id DESC LIMIT 1",
            (user_id,))
        row = await cur.fetchone()
        return (row['id'], row['admin_id']) if row else None

async def find_open_ticket_by_user(user_id: int):
    async with aiosqlite.connect('tg_bot.db') as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT id, status FROM tickets WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        return await cur.fetchone()

async def find_active_ticket_by_admin(admin_id: int):
    async with aiosqlite.connect('tg_bot.db') as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, user_id FROM tickets WHERE admin_id = ? AND status = 'accepted' ORDER BY id DESC LIMIT 1",
            (admin_id,))
        row = await cur.fetchone()
        return (row['id'], row['user_id']) if row else None

# Хендлер: создание тикета (заменяет старые обработчики)
@rt.message(F.text)
async def support_request_handler(message: Message):
    """
    Обрабатывает 'Поддержка' или команду '/support'.
    Если текст не соответствует — возвращает управление другим хендлерам.
    """
    try:
        text = (message.text or "").strip().lower()
        if text not in ("поддержка", "/support"):
            return  # не наш хендлер

        user_id = message.from_user.id
        logger.info(f"support_request_handler: запрос от {user_id}, text='{message.text}'")

        # Проверяем существующий тикет
        existing = await find_open_ticket_by_user(user_id)
        if existing and existing['status'] in ('open', 'accepted'):
            await message.answer(
                "У вас уже есть открытый запрос. Подождите ответа администратора или завершите текущий чат командой /end.",
                reply_markup=kb.get_main_menu()
            )
            return

        ticket_id = await create_ticket(user_id)
        await message.answer("Запрос отправлен в техподдержку. Ожидайте — администратор примет чат.", reply_markup=types.ReplyKeyboardRemove())
        logger.info(f"support: создан тикет #{ticket_id} для {user_id}")

        # Уведомляем админов (используется твоя get_admin_ids() или db_admin)
        # если у тебя есть get_admin_ids() — он будет использован; иначе используй db_admin.get_admins() по своему коду
        try:
            admin_ids = await get_admin_ids()
        except Exception:
            admin_ids = []
            logger.exception("Не удалось получить список админов через get_admin_ids()")

        logger.info(f"support: admin_ids = {admin_ids}")
        if not admin_ids:
            await message.answer("Извините, сейчас нет доступных администраторов. Попробуйте позже.", reply_markup=kb.get_main_menu())
            return

        text_to_admin = (
            f"🆕 Новый запрос поддержки — тикет #{ticket_id}\n"
            f"Пользователь: <a href='tg://user?id={user_id}'>пользователь</a>\n"
            "Нажмите «Принять», чтобы взять чат."
        )
        kb_accept = kb.support_admin_accept_kb(ticket_id)
        for adm in admin_ids:
            try:
                await message.bot.send_message(adm, text_to_admin, reply_markup=kb_accept, parse_mode='HTML')
                logger.info(f"support: уведомление админу {adm} отправлено (ticket #{ticket_id})")
            except Exception as e:
                logger.warning(f"support: не удалось уведомить админа {adm}: {e}")

    except Exception as e:
        logger.exception(f"support_request_handler error: {e}")
        await message.answer("Произошла ошибка при создании запроса.", reply_markup=kb.get_main_menu())

# Callback: принять тикет
@rt.callback_query(F.data.startswith("support_accept:"))
async def cb_support_accept(callback: CallbackQuery):
    try:
        admin_id = callback.from_user.id
        if not await db_admin.is_admin(admin_id):
            await callback.answer("Только админы могут принимать заявки.", show_alert=True)
            return
        ticket_id = int(callback.data.split(":", 1)[1])
        ticket = await get_ticket(ticket_id)
        if not ticket:
            await callback.answer("Тикет не найден.", show_alert=True)
            return
        if ticket['status'] == 'accepted':
            await callback.answer("Этот тикет уже принят другим админом.", show_alert=True)
            return

        await set_ticket_admin(ticket_id, admin_id)
        user_id = ticket['user_id']

        try:
            await callback.message.edit_text(callback.message.text + f"\n\n✅ Принят админом <a href='tg://user?id={admin_id}'>здесь</a>.", parse_mode='HTML')
        except Exception:
            pass

        await callback.answer("Вы приняли тикет.")
        try:
            await callback.bot.send_message(admin_id, f"Вы подключены к тикету #{ticket_id}. Чтобы завершить чат — нажмите кнопку или отправьте /end.", reply_markup=kb.support_in_chat_kb())
        except Exception:
            pass
        try:
            await callback.bot.send_message(user_id, "Админ принял ваш запрос. Вы можете писать сообщения в этот чат. Чтобы завершить — нажмите «Завершить чат» или отправьте /end.", reply_markup=kb.support_in_chat_kb())
        except Exception:
            pass

    except Exception as e:
        logger.exception(f"cb_support_accept error: {e}")
        await callback.answer("Произошла ошибка.", show_alert=True)

# Callback: отклонить тикет
@rt.callback_query(F.data.startswith("support_reject:"))
async def cb_support_reject(callback: CallbackQuery):
    try:
        admin_id = callback.from_user.id
        if not await db_admin.is_admin(admin_id):
            await callback.answer("Только админы могут отклонять заявки.", show_alert=True)
            return
        ticket_id = int(callback.data.split(":", 1)[1])
        ticket = await get_ticket(ticket_id)
        if not ticket:
            await callback.answer("Тикет не найден.", show_alert=True)
            return
        try:
            await callback.message.edit_text(callback.message.text + f"\n\n❌ Отклонён админом <a href='tg://user?id={admin_id}'>здесь</a>.", parse_mode='HTML')
        except Exception:
            pass
        await callback.answer("Отклонено.")
    except Exception as e:
        logger.exception(f"cb_support_reject error: {e}")
        await callback.answer("Произошла ошибка.", show_alert=True)

# Callback: завершить чат
@rt.callback_query(F.data == "support_end")
async def cb_support_end(callback: CallbackQuery):
    try:
        user = callback.from_user
        active_admin = await find_active_ticket_by_admin(user.id)
        if active_admin:
            ticket_id, client_id = active_admin
            await close_ticket(ticket_id)
            await callback.bot.send_message(client_id, "Чат завершён администратором.", reply_markup=kb.get_main_menu())
            await callback.bot.send_message(user.id, "Вы завершили чат.", reply_markup=kb.get_main_menu())
            await callback.answer("Чат завершён.")
            return

        active_client = await find_active_ticket_by_user(user.id)
        if active_client:
            ticket_id, admin_id = active_client
            await close_ticket(ticket_id)
            await callback.bot.send_message(admin_id, "Клиент завершил чат.", reply_markup=kb.get_main_menu())
            await callback.bot.send_message(user.id, "Вы завершили чат.", reply_markup=kb.get_main_menu())
            await callback.answer("Чат завершён.")
            return

        await callback.answer("У вас нет активных чатов.", show_alert=True)
    except Exception as e:
        logger.exception(f"cb_support_end error: {e}")
        await callback.answer("Произошла ошибка.", show_alert=True)

# Реле сообщений (админ <-> клиент)
@rt.message()
async def support_relay_messages(message: Message):
    try:
        user_id = message.from_user.id
        text = (message.text or "").strip()

        # 1) если админ отправляет сообщение
        if await db_admin.is_admin(user_id):
            active = await find_active_ticket_by_admin(user_id)
            if not active:
                return
            ticket_id, client_id = active
            if text.lower() == "/end":
                await close_ticket(ticket_id)
                await message.answer("Вы завершили чат.", reply_markup=kb.get_main_menu())
                await message.bot.send_message(client_id, "Админ завершил чат.", reply_markup=kb.get_main_menu())
                return

            try:
                await message.bot.copy_message(chat_id=client_id, from_chat_id=message.chat.id, message_id=message.message_id)
            except Exception:
                await message.bot.forward_message(chat_id=client_id, from_chat_id=message.chat.id, message_id=message.message_id)
            return

        # 2) если обычный пользователь (клиент)
        active_user = await find_active_ticket_by_user(user_id)
        if not active_user:
            if text.lower() in ("поддержка", "/support"):
                await support_request_handler(message)
            return

        ticket_id, admin_id = active_user
        if text.lower() == "/end":
            await close_ticket(ticket_id)
            await message.answer("Вы завершили чат.", reply_markup=kb.get_main_menu())
            await message.bot.send_message(admin_id, "Клиент завершил чат.", reply_markup=kb.get_main_menu())
            return

        try:
            await message.bot.copy_message(chat_id=admin_id, from_chat_id=message.chat.id, message_id=message.message_id)
        except Exception:
            await message.bot.forward_message(chat_id=admin_id, from_chat_id=message.chat.id, message_id=message.message_id)

    except Exception as e:
        logger.exception(f"support_relay_messages error: {e}")



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
# --- АНАЛИТИКА / СТАТИСТИКА ---


@rt.callback_query(F.data == "admin_analytics")
async def admin_analytics(callback: CallbackQuery):
    """
    Обработчик кнопки 'Аналитика' в админ-меню.
    Показывает краткую сводку + подменю аналитики.
    """
    logger.info(f"Нажата кнопка 'Аналитика' от пользователя {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return

        ok_global, text_global, _ = await db_admin.get_global_order_stats()

        if not ok_global:
            text_global = "Не удалось получить общую статистику."

        await callback.message.answer(
            text_global + "\n\nВыберите тип аналитики:",
            reply_markup=kb.get_admin_analytics_menu(),
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_analytics: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


# ---------- КНОПКА: Общая статистика ----------

@rt.callback_query(F.data == "admin_analytics_global")
async def admin_analytics_global(callback: CallbackQuery):
    logger.info(f"Нажата 'Общая статистика' от {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return

        ok, text, _ = await db_admin.get_global_order_stats()
        if not ok:
            text = f"Не удалось получить статистику.\n{text}"

        await callback.message.answer(text, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_analytics_global: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


# ---------- КНОПКА: По дням (7 дней) ----------

@rt.callback_query(F.data == "admin_analytics_daily")
async def admin_analytics_daily(callback: CallbackQuery):
    logger.info(f"Нажата 'По дням' от {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return

        ok, text, _ = await db_admin.get_daily_order_stats(limit=7)
        if not ok:
            text = f"Не удалось получить статистику по дням.\n{text}"

        await callback.message.answer(text, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_analytics_daily: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)


# ---------- КНОПКА: По пользователю ----------

@rt.callback_query(F.data == "admin_analytics_user")
async def admin_analytics_user(callback: CallbackQuery):
    """
    При нажатии 'По пользователю' показываем список всех user_id
    и по каждому: сколько заказов и статусы.
    """
    logger.info(f"Нажата 'По пользователю' от {callback.from_user.id}")
    try:
        if not await db_admin.is_admin(callback.from_user.id):
            await callback.answer("Эта команда доступна только администратору.", show_alert=True)
            return

        ok, text, _ = await db_admin.get_users_overview()
        if not ok:
            text = f"Не удалось получить статистику по пользователям.\n{text}"

        await callback.message.answer(text, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в обработчике admin_analytics_user: {e}", exc_info=True)
        await callback.answer("Произошла ошибка.", show_alert=True)

@rt.message(Command("stats"))
async def cmd_stats(message: Message):
    """
    /stats – общая статистика по заказам.
    Только для администраторов.
    """
    user_id = message.from_user.id
    logger.info(f"/stats от пользователя {user_id}")
    try:
        if not await db_admin.is_admin(user_id):
            await message.answer("Эта команда доступна только администратору.")
            return

        ok, text, _ = await db_admin.get_global_order_stats()
        if ok:
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer(f"Не удалось получить статистику.\n{text}")

    except Exception as e:
        logger.error(f"Ошибка в команде /stats: {e}", exc_info=True)
        await message.answer("Произошла ошибка при получении статистики.")


@rt.message(Command("daily_stats"))
async def cmd_daily_stats(message: Message, command: CommandObject):
    """
    /daily_stats [дней] – статистика по дням.
    Пример: /daily_stats 5
    По умолчанию 7 дней.
    Только для администраторов.
    """
    user_id = message.from_user.id
    logger.info(f"/daily_stats от пользователя {user_id} с аргументами: {command.args!r}")
    try:
        if not await db_admin.is_admin(user_id):
            await message.answer("Эта команда доступна только администратору.")
            return

        days = 7
        if command.args:
            try:
                days = int(command.args.split()[0])
                if days <= 0:
                    raise ValueError
            except ValueError:
                await message.answer("Некорректное число дней. Пример: /daily_stats 7")
                return

        ok, text, _ = await db_admin.get_daily_order_stats(limit=days)
        if ok:
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer(f"Не удалось получить статистику по дням.\n{text}")

    except Exception as e:
        logger.error(f"Ошибка в команде /daily_stats: {e}", exc_info=True)
        await message.answer("Произошла ошибка при получении статистики по дням.")


@rt.message(Command("user_stats"))
async def cmd_user_stats(message: Message, command: CommandObject):
    """
    /user_stats <user_id> – статистика по конкретному пользователю (Telegram user_id).
    Пример: /user_stats 1155154067
    Только для администраторов.
    """
    admin_id = message.from_user.id
    logger.info(f"/user_stats от пользователя {admin_id} с аргументами: {command.args!r}")
    try:
        if not await db_admin.is_admin(admin_id):
            await message.answer("Эта команда доступна только администратору.")
            return

        if not command.args:
            await message.answer("Использование: /user_stats <user_id>\nПример: /user_stats 1155154067")
            return

        try:
            target_user_id = int(command.args.split()[0])
        except ValueError:
            await message.answer("user_id должен быть числом. Пример: /user_stats 1155154067")
            return

        ok, text, data = await db_admin.get_user_order_stats(target_user_id)
        if ok:
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer(f"Не удалось получить статистику пользователя.\n{text}")

    except Exception as e:
        logger.error(f"Ошибка в команде /user_stats: {e}", exc_info=True)
        await message.answer("Произошла ошибка при получении статистики по пользователю.")


