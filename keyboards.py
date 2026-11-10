from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from database import get_active_games, get_game_ranks, get_game_roles


def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="🔍 Найти напарника")],
            [KeyboardButton(text="📬 Входящие")],
            [KeyboardButton(text="✏️ Заполнить профиль")],
            [KeyboardButton(text="👨‍💻 О разработчике")],
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


def ranks_menu(game_name: str):
    ranks = get_game_ranks(game_name)

    if not ranks:
        return None

    keyboard = []
    row = []
    for rank in ranks:
        row.append(KeyboardButton(text=rank))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def roles_menu(game_name: str = None):
    if not game_name:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Керри"), KeyboardButton(text="Саппорт")],
                [KeyboardButton(text="Мид"), KeyboardButton(text="Оффлейн")],
                [KeyboardButton(text="⬅️ Назад")],
            ],
            resize_keyboard=True
        )
        return kb

    roles = get_game_roles(game_name)

    if not roles:
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Керри"), KeyboardButton(text="Саппорт")],
                [KeyboardButton(text="Мид"), KeyboardButton(text="Оффлейн")],
                [KeyboardButton(text="⬅️ Назад")],
            ],
            resize_keyboard=True
        )
        return kb

    keyboard = []
    row = []
    for role in roles:
        row.append(KeyboardButton(text=role))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


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
                InlineKeyboardButton(text="🔥 По стилю", callback_data="filter:style"),
                InlineKeyboardButton(text="🎯 По цели", callback_data="filter:goal"),
            ],
            [
                InlineKeyboardButton(text="🎤 По голосу", callback_data="filter:voice"),
                InlineKeyboardButton(text="📊 По опыту", callback_data="filter:experience"),
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
                InlineKeyboardButton(text="🔥 Стиль", callback_data="filter:style"),
                InlineKeyboardButton(text="🎯 Цель", callback_data="filter:goal"),
            ],
            [
                InlineKeyboardButton(text="🎤 Голос", callback_data="filter:voice"),
                InlineKeyboardButton(text="📊 Опыт", callback_data="filter:experience"),
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
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 1", callback_data=f"rating:stars:1:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐ 2", callback_data=f"rating:stars:2:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data=f"rating:stars:3:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data=f"rating:stars:4:{to_user_id}"),
                InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data=f"rating:stars:5:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="rating:cancel"),
            ],
        ]
    )
    return kb


def rating_tags_menu(to_user_id: int, stars: int, selected_tags: list = None):
    if selected_tags is None:
        selected_tags = []

    positive = [
        ("🎯 Хороший саппорт", "🎯 Хороший саппорт"),
        ("😄 Веселый", "😄 Веселый"),
        ("🧠 Ментор", "🧠 Ментор"),
        ("🤝 Командный", "🤝 Командный"),
    ]

    negative = [
        ("😡 Токсик", "😡 Токсик"),
        ("🚪 Ливер", "🚪 Ливер"),
        ("🤐 Молчал", "🤐 Молчал"),
    ]

    keyboard = []

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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="rating:menu")],
        ]
    )


# ===== ЖАЛОБЫ =====

def report_reasons_menu(to_user_id: int):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="😡 Оскорбления", callback_data=f"report:reason:Оскорбления:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="🚪 Ливерство", callback_data=f"report:reason:Ливерство:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="📢 Спам", callback_data=f"report:reason:Спам:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="💤 AFK", callback_data=f"report:reason:AFK:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="🎮 Читы", callback_data=f"report:reason:Читы:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Другое", callback_data=f"report:reason:Другое:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Отмена", callback_data="report:cancel"),
            ],
        ]
    )
    return kb


def report_confirm_menu(to_user_id: int, reason: str):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, пожаловаться", callback_data=f"report:confirm:{reason}:{to_user_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"report:back:{to_user_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="report:cancel"),
            ],
        ]
    )
    return kb


def report_done_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="report:menu")],
        ]
    )


def admin_reports_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Последние жалобы", callback_data="admin:reports:0")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="admin:menu")],
        ]
    )


# ===== СООБЩЕНИЯ =====

def inbox_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="inbox:refresh")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="inbox:menu")],
        ]
    )


def chat_actions_menu(other_user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Написать",
                    callback_data=f"chat:write:{other_user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить диалог",
                    callback_data=f"chat:delete:{other_user_id}"
                ),
                InlineKeyboardButton(
                    text="🚫 Заблокировать",
                    callback_data=f"chat:block:{other_user_id}"
                ),
            ],
            [
                InlineKeyboardButton(text="🏠 В меню", callback_data="chat:menu"),
            ],
        ]
    )


def block_confirm_menu(other_user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, заблокировать",
                    callback_data=f"chat:block_confirm:{other_user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"chat:view:{other_user_id}"
                ),
            ],
        ]
    )


def unblock_menu(other_user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Разблокировать",
                    callback_data=f"chat:unblock:{other_user_id}"
                ),
            ],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="chat:menu")],
        ]
    )


def delete_confirm_menu(other_user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Да, удалить",
                    callback_data=f"chat:delete_confirm:{other_user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"chat:view:{other_user_id}"
                ),
            ],
        ]
    )


def blocked_list_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="chat:menu")],
        ]
    )


# ===== О РАЗРАБОТЧИКЕ =====

def developer_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Twitch",
                    url="https://www.twitch.tv/raise_nik"
                ),
                InlineKeyboardButton(
                    text="▶️ YouTube",
                    url="https://youtube.com/@raise1nik?si=C02DLIANh_GX0DfP"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📸 Instagram",
                    url="https://www.instagram.com/raise1nik?exln=ZHkwNml6ejR5ajF2&utm_source=qr"
                ),
                InlineKeyboardButton(
                    text="🎵 TikTok",
                    url="https://www.tiktok.com/@raise2nik"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💖 Поддержать проект",
                    url="https://www.donationalerts.com/r/raise_nik"
                ),
            ],
        ]
    )
    return kb


# ===== РАСШИРЕННЫЙ ПРОФИЛЬ =====

def style_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Агрессивный")],
            [KeyboardButton(text="Тактический")],
            [KeyboardButton(text="Фан")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    return kb


def goal_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Победа")],
            [KeyboardButton(text="Обучение")],
            [KeyboardButton(text="Веселье")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    return kb


def voice_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Есть микрофон")],
            [KeyboardButton(text="Готов говорить")],
            [KeyboardButton(text="Без голоса")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    return kb


def experience_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Новичок")],
            [KeyboardButton(text="Средний")],
            [KeyboardButton(text="Про")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
    return kb


# ===== ФИЛЬТРЫ РАСШИРЕННОГО ПРОФИЛЯ =====

def filter_style_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Агрессивный", callback_data="filter:style_set:Агрессивный")],
            [InlineKeyboardButton(text="Тактический", callback_data="filter:style_set:Тактический")],
            [InlineKeyboardButton(text="Фан", callback_data="filter:style_set:Фан")],
            [InlineKeyboardButton(text="Любой стиль", callback_data="filter:style_set:any")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:menu")],
        ]
    )
    return kb


def filter_goal_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Победа", callback_data="filter:goal_set:Победа")],
            [InlineKeyboardButton(text="Обучение", callback_data="filter:goal_set:Обучение")],
            [InlineKeyboardButton(text="Веселье", callback_data="filter:goal_set:Веселье")],
            [InlineKeyboardButton(text="Любая цель", callback_data="filter:goal_set:any")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:menu")],
        ]
    )
    return kb


def filter_voice_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Есть микрофон", callback_data="filter:voice_set:Есть микрофон")],
            [InlineKeyboardButton(text="Готов говорить", callback_data="filter:voice_set:Готов говорить")],
            [InlineKeyboardButton(text="Без голоса", callback_data="filter:voice_set:Без голоса")],
            [InlineKeyboardButton(text="Любой", callback_data="filter:voice_set:any")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:menu")],
        ]
    )
    return kb


def filter_experience_menu():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Новичок", callback_data="filter:experience_set:Новичок")],
            [InlineKeyboardButton(text="Средний", callback_data="filter:experience_set:Средний")],
            [InlineKeyboardButton(text="Про", callback_data="filter:experience_set:Про")],
            [InlineKeyboardButton(text="Любой опыт", callback_data="filter:experience_set:any")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:menu")],
        ]
    )
    return kb


# ===== МЕНТОР =====

def mentor_menu():
    """Меню ментора."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Стать ментором", callback_data="mentor:become")],
            [InlineKeyboardButton(text="🔍 Найти ментора", callback_data="mentor:find")],
            [InlineKeyboardButton(text="👤 Мой профиль ментора", callback_data="mentor:profile")],
            [InlineKeyboardButton(text="❌ Перестать быть ментором", callback_data="mentor:leave")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="mentor:menu")],
        ]
    )


def mentor_find_menu():
    """Меню поиска ментора."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎮 По игре", callback_data="mentor:filter:game")],
            [InlineKeyboardButton(text="🎯 По роли", callback_data="mentor:filter:role")],
            [InlineKeyboardButton(text="🕐 По времени", callback_data="mentor:filter:time")],
            [InlineKeyboardButton(text="🔍 Искать", callback_data="mentor:search")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="mentor:menu")],
        ]
    )


def mentor_review_menu(mentor_id: int):
    """Меню оценки ментора."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ 1", callback_data=f"mentor:review:1:{mentor_id}"),
                InlineKeyboardButton(text="⭐⭐ 2", callback_data=f"mentor:review:2:{mentor_id}"),
                InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data=f"mentor:review:3:{mentor_id}"),
                InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data=f"mentor:review:4:{mentor_id}"),
                InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data=f"mentor:review:5:{mentor_id}"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"mentor:view:{mentor_id}")],
        ]
    )


def mentor_actions_menu(mentor_id: int):
    """Действия с ментором."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Написать", callback_data=f"mentor:msg:{mentor_id}")],
            [InlineKeyboardButton(text="⭐ Оценить", callback_data=f"mentor:rate:{mentor_id}")],
            [InlineKeyboardButton(text="📋 Отзывы", callback_data=f"mentor:reviews:{mentor_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="mentor:search")],
        ]
    )


# ===== МЕНТОР: ВЫБОР ИГР И РОЛЕЙ =====

def mentor_games_menu():
    """Кнопки выбора игр для ментора (мульти-выбор)."""
    games = get_active_games()

    keyboard = []
    row = []
    for game_id, name, emoji in games:
        row.append(InlineKeyboardButton(
            text=f"{emoji} {name}",
            callback_data=f"mentor_game_toggle:{name}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="✅ Готово", callback_data="mentor_games_done")])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="mentor:menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def mentor_roles_menu(game_name: str, selected_roles: list = None):
    """Кнопки выбора ролей для ментора (мульти-выбор)."""
    if selected_roles is None:
        selected_roles = []

    roles = get_game_roles(game_name)

    if not roles:
        return None

    keyboard = []
    row = []
    for role in roles:
        label = f"✅ {role}" if role in selected_roles else role
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=f"mentor_role_toggle:{role}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="✅ Готово", callback_data="mentor_roles_done")])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="mentor:menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def mentor_time_menu():
    """Кнопки выбора времени для ментора (мульти-выбор)."""
    times = ["Утро", "День", "Вечер", "Ночь"]

    keyboard = []
    row = []
    for t in times:
        row.append(InlineKeyboardButton(
            text=t,
            callback_data=f"mentor_time_toggle:{t}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="✅ Готово", callback_data="mentor_time_done")])
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="mentor:menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)