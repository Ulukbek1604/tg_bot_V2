from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Каталог"),
                KeyboardButton(text="Поиск")
            ],
            [
                KeyboardButton(text="Поддержка")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_admin_main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    if is_admin:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Админ панель", callback_data="admin_panel")]
        ])
    return None

def get_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Жанр: Все", callback_data="filter_genre_none"),
            InlineKeyboardButton(text="Жанр: Action", callback_data="filter_genre_Action"),
            InlineKeyboardButton(text="Жанр: RPG", callback_data="filter_genre_RPG")
        ],
        [
            InlineKeyboardButton(text="Цена: Без фильтра", callback_data="filter_price_none"),
            InlineKeyboardButton(text="Цена: до 10$", callback_data="filter_price_10"),
            InlineKeyboardButton(text="Цена: до 20$", callback_data="filter_price_20")
        ]
    ])

def get_game_actions_keyboard(game_id: int, item_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить", callback_data=f"buy_{game_id}")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_catalog")]
    ])

def get_order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data=f"complete_{order_id}"),
            InlineKeyboardButton(text="Отменить", callback_data=f"cancel_{order_id}")
        ]
    ])

def get_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Добавить продукт", callback_data="admin_add_product"),
            InlineKeyboardButton(text="Редактировать продукт", callback_data="admin_edit_product")
        ],
        [
            InlineKeyboardButton(text="Удалить продукт", callback_data="admin_delete_product"),
            InlineKeyboardButton(text="Установить скидку", callback_data="admin_set_discount")
        ],
        [
            InlineKeyboardButton(text="Заказы", callback_data="admin_orders"),
            InlineKeyboardButton(text="Управление админами", callback_data="admin_manage_users")
        ],
        [
            InlineKeyboardButton(text="Добавить админа", callback_data="admin_add_admin"),
            InlineKeyboardButton(text="Удалить админа", callback_data="admin_remove_admin")
        ],
        [
            InlineKeyboardButton(text="Аналитика", callback_data="admin_analytics")
        ]
    ])