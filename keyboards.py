from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from database import get_active_games


def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🔍 Найти напарника")],
            [KeyboardButton(text="📬 Входящие")],
            [KeyboardButton(text="✏️ Заполнить профиль")],
        ],
        resize_keyboard=True
    )
    return kb


def games_menu():
    games = get_active_games()

    keyboard = []
    row = []
    for game_id, name, emoji in games:
        row.append(KeyboardButton(text=f"{emoji} {name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="⬅️ Назад")])

    kb = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    return kb


def games_inline_menu():
    games = get_active_games()

    keyboard = []
    row = []
    for game_id, name, emoji in games:
        row.append(InlineKeyboardButton(
            text=f"{emoji} {name}",
            callback_data=f"game_select:{name}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="game_back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def roles_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Керри"), KeyboardButton(text="Саппорт")],
            [KeyboardButton(text="Мид"), KeyboardButton(text="Оффлейн")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    return kb


def time_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Утро"), KeyboardButton(text="День")],
            [KeyboardButton(text="Вечер"), KeyboardButton(text="Ночь")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    return kb


def rating_menu(to_user_id):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐", callback_data=f"rate:1:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐", callback_data=f"rate:2:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rate:3:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rate:4:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rate:5:{to_user_id}"),
            ]
        ]
    )
    return kb


# ===== ФИЛЬТРЫ ПОИСКА =====

def filter_main_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡ Быстрый поиск", callback_data="filter:quick"),
            ],
            [
                InlineKeyboardButton(text="🎯 По игре и рангу", callback_data="filter:game"),
                InlineKeyboardButton(text="👤 По роли", callback_data="filter:role"),
            ],
            [
                InlineKeyboardButton(text="🕐 По времени", callback_data="filter:time"),
                InlineKeyboardButton(text="⭐ По рейтингу", callback_data="filter:rating"),
            ],
            [
                InlineKeyboardButton(text="🚫 Без токсиков", callback_data="filter:no_toxic"),
            ],
            [
                InlineKeyboardButton(text="🔍 Все фильтры", callback_data="filter:all"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:back"),
            ],
        ]
    )
    return kb


def filter_roles_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Керри", callback_data="filter:role_set:Керри"),
                InlineKeyboardButton(text="Саппорт", callback_data="filter:role_set:Саппорт"),
            ],
            [
                InlineKeyboardButton(text="Мид", callback_data="filter:role_set:Мид"),
                InlineKeyboardButton(text="Оффлейн", callback_data="filter:role_set:Оффлейн"),
            ],
            [
                InlineKeyboardButton(text="Любая роль", callback_data="filter:role_set:any"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:menu"),
            ],
        ]
    )
    return kb


def filter_time_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Утро", callback_data="filter:time_set:Утро"),
                InlineKeyboardButton(text="День", callback_data="filter:time_set:День"),
            ],
            [
                InlineKeyboardButton(text="Вечер", callback_data="filter:time_set:Вечер"),
                InlineKeyboardButton(text="Ночь", callback_data="filter:time_set:Ночь"),
            ],
            [
                InlineKeyboardButton(text="Любое время", callback_data="filter:time_set:any"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:menu"),
            ],
        ]
    )
    return kb


def filter_rating_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="0+", callback_data="filter:rating_set:0"),
                InlineKeyboardButton(text="3+", callback_data="filter:rating_set:3"),
                InlineKeyboardButton(text="5+", callback_data="filter:rating_set:5"),
            ],
            [
                InlineKeyboardButton(text="6+", callback_data="filter:rating_set:6"),
                InlineKeyboardButton(text="7+", callback_data="filter:rating_set:7"),
                InlineKeyboardButton(text="8+", callback_data="filter:rating_set:8"),
            ],
            [
                InlineKeyboardButton(text="Любой рейтинг", callback_data="filter:rating_set:any"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:menu"),
            ],
        ]
    )
    return kb


def filter_results_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Новый поиск", callback_data="filter:menu"),
            ],
            [
                InlineKeyboardButton(text="🏠 В меню", callback_data="filter:back"),
            ],
        ]
    )
    return kb


def filter_summary_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎯 Игра", callback_data="filter:game"),
                InlineKeyboardButton(text="👤 Роль", callback_data="filter:role"),
            ],
            [
                InlineKeyboardButton(text="🕐 Время", callback_data="filter:time"),
                InlineKeyboardButton(text="⭐ Рейтинг", callback_data="filter:rating"),
            ],
            [
                InlineKeyboardButton(text="🔍 Искать", callback_data="filter:search"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:menu"),
            ],
        ]
    )
    return kb

# ===== ОЦЕНКА НАПАРНИКА =====

def rating_stars_menu(to_user_id: int):
    """Меню выбора звёзд."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐", callback_data=f"rating:stars:1:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐", callback_data=f"rating:stars:2:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rating:stars:3:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rating:stars:4:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rating:stars:5:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="rating:cancel"),
            ],
        ]
    )
    return kb


def rating_tags_menu(to_user_id: int, stars: int, selected_tags: list = None):
    """
    Меню выбора тегов.
    selected_tags — список уже выбранных тегов.
    """
    if selected_tags is None:
        selected_tags = []

    # Позитивные теги
    positive = [
        ("🎯 Хороший саппорт", "🎯 Хороший саппорт"),
        ("😄 Веселый", "😄 Веселый"),
        ("🧠 Ментор", "🧠 Ментор"),
        ("🤝 Командный", "🤝 Командный"),
    ]

    # Негативные теги
    negative = [
        ("😡 Токсик", "😡 Токсик"),
        ("🚪 Ливер", "🚪 Ливер"),
        ("🤐 Молчал", "🤐 Молчал"),
    ]

    keyboard = []

    # Позитивные
    row = []
    for label, tag in positive:
        if tag in selected_tags:
            label = "✅ " + label
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=f"rating:tag_toggle:{tag}:{to_user_id}:{stars}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Негативные
    row = []
    for label, tag in negative:
        if tag in selected_tags:
            label = "✅ " + label
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=f"rating:tag_toggle:{tag}:{to_user_id}:{stars}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton(
            text="✅ Сохранить",
            callback_data=f"rating:save:{to_user_id}:{stars}"
        ),
    ])
    keyboard.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"rating:back:{to_user_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="rating:cancel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def rating_done_menu():
    """Меню после сохранения оценки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="rating:menu")],
        ]
    )