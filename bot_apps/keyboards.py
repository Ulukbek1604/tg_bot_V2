# bot_apps/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="Каталог")],
        [KeyboardButton(text="Поиск")],
        [KeyboardButton(text="Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

#
def get_admin_main_menu(is_admin: bool):
    if not is_admin:
        return None
    keyboard = [[InlineKeyboardButton(text="Админ панель", callback_data="admin_panel")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_catalog_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Steam игры", callback_data="catalog_steam_games")],
        [InlineKeyboardButton(text="Windows ключи", callback_data="catalog_windows_keys")],
        [InlineKeyboardButton(text="Office ключи", callback_data="catalog_office_keys")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_catalog_choice_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Весь список", callback_data="show_all_games")],
        [InlineKeyboardButton(text="По фильтру", callback_data="show_filters")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_filter_type_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="По цене", callback_data="filter_by_price")],
        [InlineKeyboardButton(text="По жанру", callback_data="filter_by_genre")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_price_filter_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Цена до 10$", callback_data="filter_price_10"),
         InlineKeyboardButton(text="Цена до 20$", callback_data="filter_price_20")],
        [InlineKeyboardButton(text="Цена до 50$", callback_data="filter_price_50"),
         InlineKeyboardButton(text="Без фильтра", callback_data="filter_price_none")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_genre_filter_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Экшн", callback_data="filter_genre_Экшн"),
         InlineKeyboardButton(text="Приключение", callback_data="filter_genre_Приключение")],
        [InlineKeyboardButton(text="Симулятор", callback_data="filter_genre_Симулятор"),
         InlineKeyboardButton(text="Головоломка", callback_data="filter_genre_Головоломка")],
        [InlineKeyboardButton(text="Стратегия", callback_data="filter_genre_Стратегия"),
         InlineKeyboardButton(text="Ролевые игры", callback_data="filter_genre_Ролевые игры")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_game_actions_keyboard(game_id: int, item_type: str = "game") -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(text="Купить", callback_data=f"buy_{game_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_order_{order_id}")],
        [InlineKeyboardButton(text="Отменить", callback_data=f"cancel_order_{order_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_menu() -> InlineKeyboardMarkup:
    """Главное админ-меню"""
    keyboard = [
        [InlineKeyboardButton(text="Добавить продукт", callback_data="admin_add_product"),
         InlineKeyboardButton(text="Редактировать продукт", callback_data="admin_edit_product")],
        [InlineKeyboardButton(text="Удалить продукт", callback_data="admin_delete_product"),
         InlineKeyboardButton(text="Установить скидку", callback_data="admin_set_discount")],
        [InlineKeyboardButton(text="Заказы", callback_data="admin_orders"),
         InlineKeyboardButton(text="Управление админами", callback_data="admin_manage_users")],
        [InlineKeyboardButton(text="Аналитика", callback_data="admin_analytics")],
        [InlineKeyboardButton(text="Акции на игры", callback_data="admin_sales_menu")]  # ← вот сюда
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_analytics_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Общая статистика", callback_data="admin_analytics_global")],
        [InlineKeyboardButton(text="По дням (7 дней)", callback_data="admin_analytics_daily")],
        [InlineKeyboardButton(text="По пользователю", callback_data="admin_analytics_user")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_promotions_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Создать акцию", callback_data="admin_create_promo")],
        [InlineKeyboardButton(text="Просмотреть акции", callback_data="admin_view_promos")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def support_admin_accept_kb(ticket_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Принять", callback_data=f"support_accept:{ticket_id}"),
         InlineKeyboardButton(text="Отклонить", callback_data=f"support_reject:{ticket_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def support_in_chat_kb() -> InlineKeyboardMarkup:
    keyboard = [[InlineKeyboardButton(text="Завершить чат", callback_data="support_end")]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)