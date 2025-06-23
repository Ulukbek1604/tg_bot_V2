import html
import shlex
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, CallbackQuery
import bot_apps.keyboards as kb
import bot_apps.db_user as db_user
import bot_apps.db_admin as db_admin
import logging
import aiosqlite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rt = Router()

async def send_payment_invoice(bot: Bot, user_id: int, key_id: int, game_name: str, price: float):
    await bot.send_message(
        user_id,
        html.escape(f"Платёж за {game_name} на сумму {price:.2f}$. Пожалуйста, оплатите через [ссылку](https://example.com/pay)."),
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    return True

async def get_final_price(key_id: int) -> float:
    try:
        async with aiosqlite.connect('tg_bot.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT price, discount FROM steam_keys WHERE id = ?', (key_id,))
            game = await cursor.fetchone()
            if game:
                return game['price'] * (1 - game['discount'] / 100)
            return 0.0
    except Exception as e:
        logger.error(f"Ошибка получения цены для key_id={key_id}: {str(e)}")
        return 0.0

@rt.message(CommandStart())
async def start(message: Message):
    logger.info(f"Команда /start от пользователя {message.from_user.id}")
    try:
        is_admin = await db_admin.is_admin(message.from_user.id)
        main_menu = kb.get_main_menu()
        admin_menu = kb.get_admin_main_menu(is_admin)
        await message.reply(
            html.escape(f"Привет, '{message.from_user.full_name}'! Это бот для покупки Steam ключей и аккаунтов (ID: {message.from_user.id})"),
            reply_markup=main_menu,
            parse_mode='HTML'
        )
        if admin_menu:
            await message.answer(
                "Админ-меню доступно:",
                reply_markup=admin_menu
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике /start: {str(e)}")
        await message.reply("Произошла ошибка. Попробуйте позже.")

@rt.message(F.text == 'Каталог')
async def catalog(message: Message):
    logger.info(f"Нажата кнопка 'Каталог' от пользователя {message.from_user.id}")
    try:
        await message.answer(
            "Выберите фильтры или просмотрите каталог:",
            reply_markup=kb.get_filter_keyboard()
        )
        success, msg, games = await db_user.show_all_games()
        if success and games:
            for game in games:
                game_id = int(game.split("\n")[0].replace("*ID*: ", ""))
                await message.answer(
                    html.escape(game),
                    reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                    parse_mode='HTML'
                )
        else:
            await message.answer(
                html.escape(msg),
                reply_markup=kb.get_main_menu(),
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике каталога: {str(e)}")
        await message.answer("Произошла ошибка при загрузке каталога.")

@rt.message(F.text == 'Поиск')
async def search_button(message: Message):
    logger.info(f"Нажата кнопка 'Поиск' от пользователя {message.from_user.id}")
    await message.answer(
        "Введите название игры для поиска:",
        reply_markup=kb.get_main_menu()
    )

@rt.message(Command('search'))
async def search(message: Message):
    logger.info(f"Команда /search от пользователя {message.from_user.id}")
    await message.answer(
        "Введите название игры для поиска:",
        reply_markup=kb.get_main_menu()
    )

@rt.message(F.text == 'Поддержка')
async def support_button(message: Message):
    logger.info(f"Нажата кнопка 'Поддержка' от пользователя {message.from_user.id}")
    await message.answer(
        "Для связи с поддержкой напишите нам в @SupportChannel или на email support@example.com.",
        reply_markup=kb.get_main_menu()
    )

@rt.message(Command('support'))
async def support(message: Message):
    logger.info(f"Команда /support от пользователя {message.from_user.id}")
    await message.answer(
        "Для связи с поддержкой напишите нам в @SupportChannel или на email support@example.com.",
        reply_markup=kb.get_main_menu()
    )

@rt.message(F.text.regexp(r'^(?!/)(.+)$'))
async def search_query(message: Message):
    query = message.text.strip()
    logger.info(f"Поиск по запросу '{query}' от пользователя {message.from_user.id}")
    if query in ['Каталог', 'Поиск', 'Поддержка']:
        logger.info(f"Сообщение '{query}' является командой меню, игнорируем")
        return
    success, msg, games = await db_user.search_games(query)
    if success and games:
        for game in games:
            game_id = int(game.split("\n")[0].replace("*ID*: ", ""))
            await message.answer(
                html.escape(game),
                reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                parse_mode='HTML'
            )
        await message.answer(
            "Выберите фильтры или просмотрите каталог:",
            reply_markup=kb.get_filter_keyboard()
        )
    else:
        await message.answer(
            html.escape(msg),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )

@rt.message(Command('buy'))
async def buy(message: Message, bot: Bot):
    try:
        logger.info(f"Команда /buy от пользователя {message.from_user.id}")
        args = shlex.split(message.text)[1:]  # Парсим аргументы с поддержкой кавычек
        if not args:
            await message.answer(
                html.escape("Формат: /buy 'ID игры'"),
                parse_mode='HTML'
            )
            return
        key_id = int(args[0])
        success, msg, game_name = await db_user.create_order(message.from_user.id, key_id)
        if success and game_name:
            await send_payment_invoice(bot, message.from_user.id, key_id, game_name, await get_final_price(key_id))
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
        logger.error(f"Ошибка в обработчике /buy: {str(e)}")
        await message.answer("Произошла ошибка при покупке.")

@rt.inline_query()
async def inline_search(query: InlineQuery):
    logger.info(f"Inline поиск от пользователя {query.from_user.id}: {query.query}")
    search_text = query.query.strip()
    success, msg, games = await db_user.search_games(search_text) if search_text else await db_user.show_all_games()
    results = [
        InlineQueryResultArticle(
            id=str(i),
            title=game.split("\n")[1].replace("*Игра*: ", ""),
            input_message_content=InputTextMessageContent(message_text=html.escape(game)),
            reply_markup=kb.get_game_actions_keyboard(int(game.split("\n")[0].replace("*ID*: ", "")), item_type="game")
        ) for i, game in enumerate(games)
    ] if success and games else []
    await query.answer(results, cache_time=1)

@rt.callback_query(F.data.startswith("filter_genre_"))
async def filter_genre(callback: CallbackQuery):
    logger.info(f"Фильтр жанра {callback.data} от пользователя {callback.from_user.id}")
    genre = callback.data.replace("filter_genre_", "").capitalize()
    success, msg, games = await db_user.show_all_games(genre=genre)
    current_text = "Выберите фильтры или просмотрите каталог:"
    current_keyboard = kb.get_filter_keyboard()
    if success and games:
        if callback.message.text != current_text or callback.message.reply_markup != current_keyboard:
            await callback.message.edit_text(
                current_text,
                reply_markup=current_keyboard
            )
        for game in games:
            game_id = int(game.split("\n")[0].replace("*ID*: ", ""))
            await callback.message.answer(
                html.escape(game),
                reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                parse_mode='HTML'
            )
    else:
        if callback.message.text != html.escape(msg) or callback.message.reply_markup != current_keyboard:
            await callback.message.edit_text(
                html.escape(msg),
                reply_markup=current_keyboard
            )
    await callback.answer()

@rt.callback_query(F.data.startswith("filter_price_"))
async def filter_price(callback: CallbackQuery):
    logger.info(f"Фильтр цены {callback.data} от пользователя {callback.from_user.id}")
    price = callback.data.replace("filter_price_", "")
    max_price = None if price == "none" else int(price)
    success, msg, games = await db_user.show_all_games(max_price=max_price)
    current_text = "Выберите фильтры или просмотрите каталог:"
    current_keyboard = kb.get_filter_keyboard()
    if success and games:
        if callback.message.text != current_text or callback.message.reply_markup != current_keyboard:
            await callback.message.edit_text(
                current_text,
                reply_markup=current_keyboard
            )
        for game in games:
            game_id = int(game.split("\n")[0].replace("*ID*: ", ""))
            await callback.message.answer(
                html.escape(game),
                reply_markup=kb.get_game_actions_keyboard(game_id, item_type="game"),
                parse_mode='HTML'
            )
    else:
        if callback.message.text != html.escape(msg) or callback.message.reply_markup != current_keyboard:
            await callback.message.edit_text(
                html.escape(msg),
                reply_markup=current_keyboard
            )
    await callback.answer()

@rt.callback_query(F.data.startswith("buy_"))
async def buy_callback(callback: CallbackQuery, bot: Bot):
    logger.info(f"Покупка {callback.data} от пользователя {callback.from_user.id}")
    key_id = int(callback.data.replace("buy_", ""))
    success, msg, game_name = await db_user.create_order(callback.from_user.id, key_id)
    if success and game_name:
        await send_payment_invoice(bot, callback.from_user.id, key_id, game_name, await get_final_price(key_id))
    await callback.message.answer(
        html.escape(msg),
        parse_mode='HTML'
    )
    await callback.answer()

@rt.callback_query(F.data.startswith("complete_"))
async def complete_order_callback(callback: CallbackQuery, bot: Bot):
    logger.info(f"Подтверждение заказа {callback.data} от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    order_id = int(callback.data.replace("complete_", ""))
    success, msg, game_name = await db_user.complete_order(order_id)
    if success:
        await bot.send_message(
            callback.from_user.id,
            html.escape(msg),
            parse_mode='HTML'
        )
    await callback.message.answer(
        html.escape(msg),
        parse_mode='HTML'
    )
    await callback.answer()

@rt.callback_query(F.data.startswith("cancel_"))
async def cancel_order_callback(callback: CallbackQuery):
    logger.info(f"Отмена заказа {callback.data} от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    order_id = int(callback.data.replace("cancel_", ""))
    success, msg = await db_user.cancel_order(order_id)
    await callback.message.answer(
        html.escape(msg),
        parse_mode='HTML'
    )
    await callback.answer()

@rt.message(Command('add_product'))
async def add_product(message: Message):
    logger.info(f"Команда /add_product от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]  # Парсим аргументы с поддержкой кавычек
        if len(args) != 6:
            await message.answer(
                html.escape("Формат: /add_product 'название игры' 'ключ' 'цена' 'количество' 'жанр' 'страна'"),
                parse_mode='HTML'
            )
            return
        game_name, st_key, price, count, genre, region = args
        price = int(price)
        count = int(count)
        if price < 0 or count < 0:
            await message.answer(
                html.escape("Цена и количество не могут быть отрицательными"),
                parse_mode='HTML'
            )
            return
        success, msg = await db_user.add_steam_key_into_db(game_name, st_key, price, count, genre, region)
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("Цена и количество должны быть числами"),
            parse_mode='HTML'
        )

@rt.message(Command('edit_product'))
async def edit_product(message: Message):
    logger.info(f"Команда /edit_product от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]  # Парсим аргументы с поддержкой кавычек
        if len(args) < 1:
            await message.answer(
                html.escape("Формат: /edit_product 'id' ['название'] ['ключ'] ['цена'] ['количество'] ['скидка'] ['жанр'] ['страна']"),
                parse_mode='HTML'
            )
            return
        key_id = int(args[0])
        game_name = args[1] if len(args) > 1 else None
        st_key = args[2] if len(args) > 2 else None
        price = int(args[3]) if len(args) > 3 and args[3] else None
        count = int(args[4]) if len(args) > 4 and args[4] else None
        discount = int(args[5]) if len(args) > 5 and args[5] else None
        genre = args[6] if len(args) > 6 else None
        region = args[7] if len(args) > 7 else None
        success, msg = await db_user.edit_steam_key_into_db(key_id, game_name, st_key, price, count, discount, genre, region)
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("ID, цена, количество и скидка должны быть числами"),
            parse_mode='HTML'
        )

@rt.message(Command('delete_product'))
async def delete_product(message: Message):
    logger.info(f"Команда /delete_product от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]  # Парсим аргументы с поддержкой кавычек
        if not args:
            await message.answer(
                html.escape("Формат: /delete_product 'ID'"),
                parse_mode='HTML'
            )
            return
        key_id = int(args[0])
        success, msg = await db_user.delete_steam_key_from_db(key_id)
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("ID должен быть числом"),
            parse_mode='HTML'
        )

@rt.message(Command('set_discount'))
async def set_discount(message: Message):
    logger.info(f"Команда /set_discount от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]  # Парсим аргументы с поддержкой кавычек
        if len(args) != 2:
            await message.answer(
                html.escape("Формат: /set_discount 'ID' 'скидка'"),
                parse_mode='HTML'
            )
            return
        key_id, discount = map(int, args)
        if not (0 <= discount <= 100):
            await message.answer(
                html.escape("Скидка должна быть от 0 до 100%"),
                parse_mode='HTML'
            )
            return
        success, msg = await db_user.edit_steam_key_into_db(key_id, discount=discount)
        await message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    except ValueError:
        await message.answer(
            html.escape("ID и скидка должны быть числами"),
            parse_mode='HTML'
        )

@rt.message(Command('orders'))
async def orders(message: Message):
    logger.info(f"Команда /orders от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    success, msg, orders = await db_user.get_orders()
    if success and orders:
        for order in orders:
            order_id = int(order.split("\n")[0].replace("*ID*: ", ""))
            await message.answer(
                html.escape(order),
                reply_markup=kb.get_order_actions_keyboard(order_id),
                parse_mode='HTML'
            )
    else:
        await message.answer(
            html.escape(msg),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )

@rt.message(Command('manage_users'))
async def manage_users(message: Message):
    logger.info(f"Команда /manage_users от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
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

@rt.message(Command('add_admin'))
async def add_admin(message: Message):
    logger.info(f"Команда /add_admin от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]  # Парсим аргументы с поддержкой кавычек
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

@rt.message(Command('remove_admin'))
async def remove_admin(message: Message):
    logger.info(f"Команда /remove_admin от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
    try:
        args = shlex.split(message.text)[1:]  # Парсим аргументы с поддержкой кавычек
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

@rt.message(Command('analytics'))
async def analytics(message: Message):
    logger.info(f"Команда /analytics от пользователя {message.from_user.id}")
    if not await db_admin.is_admin(message.from_user.id):
        await message.answer(
            html.escape("Эта команда доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        return
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

@rt.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Админ панель' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=kb.get_admin_menu()
    )
    await callback.answer()

@rt.callback_query(F.data == "admin_add_product")
async def admin_add_product_button(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Добавить продукт' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    await callback.message.answer(
        html.escape("Формат: /add_product 'название игры' 'ключ' 'цена' 'количество' 'жанр' 'страна'"),
        parse_mode='HTML'
    )
    await callback.answer()

@rt.callback_query(F.data == "admin_edit_product")
async def admin_edit_product_callback(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Редактировать продукт' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    await callback.message.answer(
        html.escape("Формат: /edit_product 'id' ['название'] ['ключ'] ['цена'] ['количество'] ['скидка'] ['жанр'] ['страна']"),
        parse_mode='HTML'
    )
    await callback.answer()

@rt.callback_query(F.data == "admin_delete_product")
async def admin_delete_product_callback(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Удалить продукт' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    await callback.message.answer(
        html.escape("Формат: /delete_product 'ID'"),
        parse_mode='HTML'
    )
    await callback.answer()

@rt.callback_query(F.data == "admin_set_discount")
async def admin_set_discount_callback(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Установить скидку' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    await callback.message.answer(
        html.escape("Формат: /set_discount 'ID' 'скидка'"),
        parse_mode='HTML'
    )
    await callback.answer()

@rt.callback_query(F.data == "admin_orders")
async def admin_orders_callback(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Заказы' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    success, msg, orders = await db_user.get_orders()
    if success and orders:
        for order in orders:
            order_id = int(order.split("\n")[0].replace("*ID*: ", ""))
            await callback.message.answer(
                html.escape(order),
                reply_markup=kb.get_order_actions_keyboard(order_id),
                parse_mode='HTML'
            )
    else:
        await callback.message.answer(
            html.escape(msg),
            parse_mode='HTML'
        )
    await callback.answer()

@rt.callback_query(F.data == "admin_manage_users")
async def admin_manage_users_callback(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Управление админами' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
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
            parse_mode='HTML'
        )
    await callback.answer()

@rt.callback_query(F.data == "admin_add_admin")
async def admin_add_admin_callback(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Добавить админа' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    await callback.message.answer(
        html.escape("Формат: /add_admin 'ID' 'Имя'"),
        parse_mode='HTML'
    )
    await callback.answer()

@rt.callback_query(F.data == "admin_remove_admin")
async def admin_remove_admin_callback(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Удалить админа' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
        return
    await callback.message.answer(
        html.escape("Формат: /remove_admin 'ID'"),
        parse_mode='HTML'
    )
    await callback.answer()

@rt.callback_query(F.data == "admin_analytics")
async def admin_analytics_callback(callback: CallbackQuery):
    logger.info(f"Нажата кнопка 'Аналитика' от пользователя {callback.from_user.id}")
    if not await db_admin.is_admin(callback.from_user.id):
        await callback.message.answer(
            html.escape("Эта функция доступна только администраторам."),
            reply_markup=kb.get_main_menu(),
            parse_mode='HTML'
        )
        await callback.answer()
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
            parse_mode='HTML'
        )
    await callback.answer()

@rt.callback_query()
async def debug_callback(callback: CallbackQuery):
    logger.info(f"Необработанный callback: {callback.data} от пользователя {callback.from_user.id}")
    await callback.answer("Команда не реализована", show_alert=True)