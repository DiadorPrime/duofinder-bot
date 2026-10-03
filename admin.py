import os
from dotenv import load_dotenv

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import (
    get_stats, get_user_stats, set_user_rating, get_user_rating,
    reset_user_rating, get_all_users, get_users_count, find_user_by_username,
    add_game, delete_game, toggle_game, get_all_games
)
from admin_keyboards import (
    admin_menu, users_pagination, user_actions, rating_values, back_to_menu
)

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

router = Router()

USERS_PER_PAGE = 10


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ===== ГЛАВНАЯ КОМАНДА =====

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет доступа к этой команде.")
        return

    await message.answer(
        "👑 <b>Админ-панель</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


# ===== СТАТИСТИКА =====

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    await send_stats(message)


@router.callback_query(F.data == "admin:stats")
async def callback_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.delete()
    await send_stats(callback.message)
    await callback.answer()


async def send_stats(message: Message):
    stats = get_stats()

    text = "📊 <b>Статистика бота</b>\n\n"

    text += f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
    text += f"🟢 Активных за 24ч: <b>{stats['active_24h']}</b>\n"
    text += f"📅 Активных за 7 дней: <b>{stats['active_7d']}</b>\n"
    text += f"✅ Заполненных профилей: <b>{stats['filled_profiles']}</b>\n\n"

    text += f"🔍 Всего поисков: <b>{stats['total_finds']}</b>\n"
    text += f"🔍 Поисков за 24ч: <b>{stats['finds_24h']}</b>\n\n"

    text += f"💬 Всего сообщений: <b>{stats.get('total_messages', 0)}</b>\n"
    text += f"💬 Сообщений за 24ч: <b>{stats.get('messages_24h', 0)}</b>\n\n"

    if stats["top_games"]:
        text += "🎮 <b>Топ игр:</b>\n"
        for game, cnt in stats["top_games"]:
            text += f"  • {game} — {cnt}\n"
        text += "\n"

    if stats["top_ranks"]:
        text += "🏆 <b>Топ рангов:</b>\n"
        for rank, cnt in stats["top_ranks"]:
            text += f"  • {rank} — {cnt}\n"
        text += "\n"

    if stats["recent_users"]:
        text += "🆕 <b>Последние регистрации:</b>\n"
        for user_id, username, created_at in stats["recent_users"][:5]:
            text += f"  • @{username} (<code>{user_id}</code>)\n"

    await message.answer(text, parse_mode="HTML", reply_markup=back_to_menu())


# ===== СПИСОК ПОЛЬЗОВАТЕЛЕЙ =====

@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    await send_users_page(message, 0)


@router.callback_query(F.data.startswith("admin:users:"))
async def callback_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    page = int(callback.data.split(":")[2])

    await callback.message.delete()
    await send_users_page(callback.message, page)
    await callback.answer()


async def send_users_page(message: Message, page: int):
    total = get_users_count()

    if total == 0:
        await message.answer("📭 Пользователей пока нет.", reply_markup=back_to_menu())
        return

    total_pages = max(1, (total + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
    offset = page * USERS_PER_PAGE

    users = get_all_users(limit=USERS_PER_PAGE, offset=offset)

    text = f"👥 <b>Пользователи</b> ({page + 1}/{total_pages})\n"
    text += f"Всего: {total}\n\n"

    for user_id, username, game, rank, rating in users:
        text += f"👤 @{username or 'без имени'}\n"
        text += f"   ID: <code>{user_id}</code>\n"
        text += f"   🎮 {game or '—'} | 🏆 {rank or '—'}\n"
        text += f"   ⭐ {rating}/10\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=users_pagination(page, total_pages))


# ===== КАРТОЧКА ПОЛЬЗОВАТЕЛЯ =====

@router.message(Command("user"))
async def cmd_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/user &lt;id&gt;</code>", parse_mode="HTML")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    await send_user_card(message, target_id)


@router.callback_query(F.data.startswith("admin:user:"))
async def callback_user(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    await callback.message.delete()
    await send_user_card(callback.message, user_id)
    await callback.answer()


async def send_user_card(message: Message, user_id: int):
    stats = get_user_stats(user_id)
    rating = get_user_rating(user_id)

    if rating is None:
        await message.answer(
            f"❌ Пользователь <code>{user_id}</code> не найден.",
            parse_mode="HTML",
            reply_markup=back_to_menu()
        )
        return

    text = f"👤 <b>Пользователь</b>\n\n"
    text += f"ID: <code>{user_id}</code>\n"
    text += f"⭐ Рейтинг: <b>{rating}/10</b>\n\n"
    text += f"🔍 Поисков: {stats['finds']}\n"
    text += f"✏️ Обновлений профиля: {stats['profile_updates']}\n"
    text += f"💬 Сообщений отправлено: {stats.get('messages_sent', 0)}\n"
    text += f"📅 Зарегистрирован: {stats['registered_at'] or '—'}\n"

    await message.answer(text, parse_mode="HTML", reply_markup=user_actions(user_id))


# ===== УПРАВЛЕНИЕ РЕЙТИНГОМ =====

@router.message(Command("set_rating"))
async def cmd_set_rating(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "Использование: <code>/set_rating &lt;user_id&gt; &lt;значение&gt;</code>\n"
            "Например: <code>/set_rating 123456789 8.5</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(parts[1])
        new_rating = float(parts[2])
    except ValueError:
        await message.answer("❌ ID и рейтинг должны быть числами.")
        return

    if new_rating < 0 or new_rating > 10:
        await message.answer("❌ Рейтинг должен быть от 0 до 10.")
        return

    success = set_user_rating(target_id, new_rating)

    if success:
        await message.answer(
            f"✅ Рейтинг пользователя <code>{target_id}</code> установлен на <b>{new_rating}/10</b>.",
            parse_mode="HTML"
        )
    else:
        await message.answer(f"❌ Пользователь <code>{target_id}</code> не найден.", parse_mode="HTML")


@router.message(Command("get_rating"))
async def cmd_get_rating(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/get_rating &lt;user_id&gt;</code>", parse_mode="HTML")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    rating = get_user_rating(target_id)

    if rating is None:
        await message.answer(f"❌ Пользователь <code>{target_id}</code> не найден.", parse_mode="HTML")
    else:
        await message.answer(
            f"⭐ Рейтинг пользователя <code>{target_id}</code>: <b>{rating}/10</b>",
            parse_mode="HTML"
        )


@router.message(Command("reset_rating"))
async def cmd_reset_rating(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: <code>/reset_rating &lt;user_id&gt;</code>", parse_mode="HTML")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    success = reset_user_rating(target_id)

    if success:
        await message.answer(
            f"✅ Рейтинг пользователя <code>{target_id}</code> сброшен на <b>5.0/10</b>.",
            parse_mode="HTML"
        )
    else:
        await message.answer(f"❌ Пользователь <code>{target_id}</code> не найден.", parse_mode="HTML")


# ===== ИНЛАЙН-КНОПКИ ДЛЯ РЕЙТИНГА =====

@router.callback_query(F.data.startswith("admin:set_rating:"))
async def callback_set_rating(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    await callback.message.edit_text(
        f"⭐ Выбери новый рейтинг для <code>{user_id}</code>:",
        parse_mode="HTML",
        reply_markup=rating_values(user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:rating_set:"))
async def callback_rating_set(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    user_id = int(parts[2])
    new_rating = float(parts[3])

    success = set_user_rating(user_id, new_rating)

    if success:
        await callback.answer(f"✅ Рейтинг установлен: {new_rating}/10", show_alert=True)
    else:
        await callback.answer("❌ Пользователь не найден", show_alert=True)

    await callback.message.delete()
    await send_user_card(callback.message, user_id)


@router.callback_query(F.data.startswith("admin:reset_rating:"))
async def callback_reset_rating(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])
    reset_user_rating(user_id)

    await callback.answer("✅ Рейтинг сброшен на 5.0", show_alert=True)

    await callback.message.delete()
    await send_user_card(callback.message, user_id)


# ===== ПОИСК ПОЛЬЗОВАТЕЛЯ =====

@router.message(Command("find_user"))
async def cmd_find_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: <code>/find_user &lt;username&gt;</code>", parse_mode="HTML")
        return

    username = parts[1].replace("@", "")
    users = find_user_by_username(username)

    if not users:
        await message.answer(f"❌ Пользователь @{username} не найден.")
        return

    text = f"🔍 <b>Найдено: {len(users)}</b>\n\n"
    for user_id, uname, game, rank, rating in users:
        text += f"👤 @{uname}\n"
        text += f"   ID: <code>{user_id}</code>\n"
        text += f"   🎮 {game or '—'} | ⭐ {rating}/10\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=back_to_menu())


# ===== УПРАВЛЕНИЕ ИГРАМИ =====

@router.message(Command("add_game"))
async def cmd_add_game(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            "Использование: <code>/add_game &lt;название&gt; [эмодзи]</code>\n"
            "Пример: <code>/add_game Overwatch 2 🛡</code>",
            parse_mode="HTML"
        )
        return

    name = parts[1]
    emoji = parts[2] if len(parts) > 2 else "🎮"

    if add_game(name, emoji):
        await message.answer(f"✅ Игра добавлена: {emoji} <b>{name}</b>", parse_mode="HTML")
    else:
        await message.answer(f"❌ Игра <b>{name}</b> уже существует.", parse_mode="HTML")


@router.message(Command("del_game"))
async def cmd_del_game(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: <code>/del_game &lt;название&gt;</code>", parse_mode="HTML")
        return

    name = parts[1]

    if delete_game(name):
        await message.answer(f"✅ Игра <b>{name}</b> удалена.", parse_mode="HTML")
    else:
        await message.answer(f"❌ Игра <b>{name}</b> не найдена.", parse_mode="HTML")


@router.message(Command("toggle_game"))
async def cmd_toggle_game(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: <code>/toggle_game &lt;название&gt;</code>", parse_mode="HTML")
        return

    name = parts[1]

    if toggle_game(name):
        await message.answer(f"✅ Активность игры <b>{name}</b> переключена.", parse_mode="HTML")
    else:
        await message.answer(f"❌ Игра <b>{name}</b> не найдена.", parse_mode="HTML")


@router.message(Command("list_games"))
async def cmd_list_games(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа.")
        return

    games = get_all_games()

    if not games:
        await message.answer("📭 Список игр пуст.")
        return

    text = "🎮 <b>Все игры</b>\n\n"
    for game_id, name, emoji, is_active in games:
        status = "🟢" if is_active else "🔴"
        text += f"{status} {emoji} <b>{name}</b>\n"
        text += f"   <code>/toggle_game {name}</code>\n\n"

    text += "\n<b>Команды:</b>\n"
    text += "<code>/add_game &lt;название&gt; [эмодзи]</code> — добавить\n"
    text += "<code>/del_game &lt;название&gt;</code> — удалить\n"
    text += "<code>/toggle_game &lt;название&gt;</code> — вкл/выкл\n"

    await message.answer(text, parse_mode="HTML", reply_markup=back_to_menu())


# ===== ПОМОЩЬ =====

@router.message(Command("admin_help"))
async def cmd_admin_help(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🛠 <b>Помощь админа</b>\n\n"
        "<b>Статистика:</b>\n"
        "/stats — общая статистика\n"
        "/admin — меню с кнопками\n\n"
        "<b>Пользователи:</b>\n"
        "/users — список (пагинация)\n"
        "/user &lt;id&gt; — карточка\n"
        "/find_user &lt;username&gt; — поиск по нику\n\n"
        "<b>Рейтинги:</b>\n"
        "/set_rating &lt;id&gt; &lt;значение&gt; — установить\n"
        "/get_rating &lt;id&gt; — посмотреть\n"
        "/reset_rating &lt;id&gt; — сбросить на 5.0\n\n"
        "<b>Игры:</b>\n"
        "/list_games — список всех игр\n"
        "/add_game &lt;название&gt; [эмодзи] — добавить\n"
        "/del_game &lt;название&gt; — удалить\n"
        "/toggle_game &lt;название&gt; — вкл/выкл\n\n"
        "<b>Сообщения (для пользователей):</b>\n"
        "/msg_&lt;id&gt; — написать\n"
        "/reply — ответить последнему\n"
        "/inbox — входящие\n"
        "/chat &lt;id&gt; — диалог\n"
        "/unread — непрочитанные\n",
        parse_mode="HTML",
        reply_markup=back_to_menu()
    )


@router.callback_query(F.data == "admin:help")
async def callback_help(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.delete()
    await cmd_admin_help(callback.message)
    await callback.answer()


@router.callback_query(F.data == "admin:ratings_help")
async def callback_ratings_help(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "⭐ <b>Управление рейтингами</b>\n\n"
        "Команды:\n"
        "<code>/set_rating &lt;id&gt; &lt;значение&gt;</code> — установить рейтинг\n"
        "<code>/get_rating &lt;id&gt;</code> — посмотреть\n"
        "<code>/reset_rating &lt;id&gt;</code> — сбросить на 5.0\n\n"
        "Или открой карточку пользователя через /users и нажми «Изменить рейтинг».",
        parse_mode="HTML",
        reply_markup=back_to_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:menu")
async def callback_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "👑 <b>Админ-панель</b>\n\n"
        "Выбери действие:",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:noop")
async def callback_noop(callback: CallbackQuery):
    await callback.answer()