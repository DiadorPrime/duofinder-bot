from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
                InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:users:0"),
            ],
            [
                InlineKeyboardButton(text="⭐ Рейтинги", callback_data="admin:ratings_help"),
                InlineKeyboardButton(text="🛠 Помощь", callback_data="admin:help"),
            ],
        ]
    )
    return kb


def users_pagination(page: int, total_pages: int):
    buttons = []

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin:users:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="admin:noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"admin:users:{page + 1}"))

    buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🏠 В меню", callback_data="admin:menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_actions(user_id: int):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ Изменить рейтинг", callback_data=f"admin:set_rating:{user_id}"),
            ],
            [
                InlineKeyboardButton(text="🔄 Сбросить рейтинг", callback_data=f"admin:reset_rating:{user_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:menu"),
            ],
        ]
    )
    return kb


def rating_values(user_id: int):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="0", callback_data=f"admin:rating_set:{user_id}:0"),
                InlineKeyboardButton(text="2", callback_data=f"admin:rating_set:{user_id}:2"),
                InlineKeyboardButton(text="4", callback_data=f"admin:rating_set:{user_id}:4"),
                InlineKeyboardButton(text="6", callback_data=f"admin:rating_set:{user_id}:6"),
            ],
            [
                InlineKeyboardButton(text="7", callback_data=f"admin:rating_set:{user_id}:7"),
                InlineKeyboardButton(text="8", callback_data=f"admin:rating_set:{user_id}:8"),
                InlineKeyboardButton(text="9", callback_data=f"admin:rating_set:{user_id}:9"),
                InlineKeyboardButton(text="10", callback_data=f"admin:rating_set:{user_id}:10"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin:user:{user_id}"),
            ],
        ]
    )
    return kb


def back_to_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="admin:menu")]
        ]
    )