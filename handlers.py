from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    add_user, update_profile, get_profile, find_partner, add_rating,
    log_event, update_last_seen,
    save_message, get_inbox, get_conversation, mark_as_read,
    count_unread, get_last_sender,
    find_partner_filtered,
    add_rating_v2, get_user_ratings, get_user_rating_stats,
    has_rated_today, recalculate_rating
)
from keyboards import (
    main_menu, games_menu, roles_menu, time_menu, rating_menu,
    filter_main_menu, filter_roles_menu, filter_time_menu,
    filter_rating_menu, filter_results_menu, filter_summary_menu,
    rating_stars_menu, rating_tags_menu, rating_done_menu
)

router = Router()


class ProfileForm(StatesGroup):
    game = State()
    rank = State()
    role = State()
    time = State()


class ChatForm(StatesGroup):
    message = State()
    reply = State()


class FilterForm(StatesGroup):
    main = State()
    role = State()
    time = State()
    rating = State()
    all = State()

class RatingForm(StatesGroup):
    stars = State()
    tags = State()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    add_user(message.from_user.id, message.from_user.username or "unknown")
    log_event(message.from_user.id, "start")
    update_last_seen(message.from_user.id)
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я помогу найти напарника для игр.\n\n"
        "📋 <b>Команды:</b>\n"
        "/profile — заполнить профиль\n"
        "/find — найти напарника\n"
        "/me — твой профиль\n"
        "/rate &lt;id&gt; — оценить напарника\n"
        "/my_rating — твоя статистика\n"
        "/recent_ratings — последние оценки\n"
        "/inbox — входящие\n"
        "/cancel — отмена",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("profile"))
@router.message(F.text == "✏️ Заполнить профиль")
async def cmd_profile(message: Message, state: FSMContext):
    await state.clear()
    update_last_seen(message.from_user.id)
    await state.set_state(ProfileForm.game)
    await message.answer("Выбери игру:", reply_markup=games_menu())


@router.message(ProfileForm.game, ~F.text.startswith("/"))
async def process_game(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return

    game_name = message.text
    parts = game_name.split(" ", 1)
    if len(parts) == 2 and not parts[0].isalnum():
        game_name = parts[1]

    await state.update_data(game=game_name)
    await state.set_state(ProfileForm.rank)
    await message.answer("Напиши свой ранг (например, 3к MMR, Gold, Diamond):")


@router.message(ProfileForm.rank, ~F.text.startswith("/"))
async def process_rank(message: Message, state: FSMContext):
    await state.update_data(rank=message.text)
    await state.set_state(ProfileForm.role)
    await message.answer("Выбери роль:", reply_markup=roles_menu())


@router.message(ProfileForm.role, ~F.text.startswith("/"))
async def process_role(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return
    await state.update_data(role=message.text)
    await state.set_state(ProfileForm.time)
    await message.answer("Когда обычно играешь?", reply_markup=time_menu())


@router.message(ProfileForm.time, ~F.text.startswith("/"))
async def process_time(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu())
        return
    await state.update_data(time=message.text)

    data = await state.get_data()
    update_profile(
        message.from_user.id,
        data["game"], data["rank"], data["role"], data["time"]
    )
    log_event(message.from_user.id, "profile_update", data["game"])
    update_last_seen(message.from_user.id)

    await state.clear()
    await message.answer(
        f"✅ Профиль сохранён!\n\n"
        f"🎮 Игра: {data['game']}\n"
        f"🏆 Ранг: {data['rank']}\n"
        f"🎯 Роль: {data['role']}\n"
        f"🕐 Время: {data['time']}",
        reply_markup=main_menu()
    )


@router.message(Command("me"))
@router.message(F.text == "👤 Профиль")
async def cmd_me(message: Message):
    update_last_seen(message.from_user.id)
    user = get_profile(message.from_user.id)
    if not user or not user[2]:
        await message.answer("Профиль пуст. Заполни: /profile")
        return

    _, username, game, rank, role, time, rating, created_at, last_seen = user
    await message.answer(
        f"👤 Твой профиль:\n\n"
        f"🎮 Игра: {game}\n"
        f"🏆 Ранг: {rank}\n"
        f"🎯 Роль: {role}\n"
        f"🕐 Время: {time}\n"
        f"⭐ Рейтинг: {rating}/10"
    )


# ===== ПОИСК С ФИЛЬТРАМИ =====

@router.message(Command("find"))
@router.message(F.text == "🔍 Найти напарника")
async def cmd_find(message: Message, state: FSMContext):
    update_last_seen(message.from_user.id)
    user = get_profile(message.from_user.id)
    if not user or not user[2]:
        await message.answer("Сначала заполни профиль: /profile")
        return

    await state.clear()
    await state.update_data(
        filter_game=user[2],
        filter_rank=user[3],
        filter_role=None,
        filter_time=None,
        filter_rating=None,
        filter_no_toxic=False,
        filter_mode="main",
    )
    await state.set_state(FilterForm.main)

    await message.answer(
        f"🔍 <b>Поиск напарника</b>\n\n"
        f"🎮 Игра: <b>{user[2]}</b>\n"
        f"🏆 Ранг: <b>{user[3]}</b>\n\n"
        f"Выбери фильтры:",
        parse_mode="HTML",
        reply_markup=filter_main_menu()
    )


@router.callback_query(F.data == "filter:back")
async def filter_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("Отменено.", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "filter:menu")
async def filter_menu(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(FilterForm.main)

    text = build_filter_summary(data)

    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=filter_main_menu()
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=filter_main_menu()
        )
    await callback.answer()


def build_filter_summary(data: dict) -> str:
    game = data.get("filter_game", "—")
    rank = data.get("filter_rank", "—")
    role = data.get("filter_role") or "любая"
    time = data.get("filter_time") or "любое"
    rating = data.get("filter_rating")
    rating_str = f"{rating}+" if rating is not None else "любой"
    no_toxic = data.get("filter_no_toxic", False)
    toxic_str = "🚫 без токсиков" if no_toxic else "все"

    return (
        f"🔍 <b>Фильтры поиска</b>\n\n"
        f"🎮 Игра: <b>{game}</b>\n"
        f"🏆 Ранг: <b>{rank}</b>\n"
        f"👤 Роль: {role}\n"
        f"🕐 Время: {time}\n"
        f"⭐ Рейтинг: {rating_str}\n"
        f"🚫 Токсики: {toxic_str}\n\n"
        f"Выбери фильтры или нажми «🔍 Искать»:"
    )


@router.callback_query(F.data == "filter:quick")
async def filter_quick(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["filter_role"] = None
    data["filter_time"] = None
    data["filter_rating"] = None
    data["filter_no_toxic"] = False
    await state.update_data(**data)

    await run_filtered_search(callback.message, callback.from_user.id, state)
    await callback.answer()


@router.callback_query(F.data == "filter:game")
async def filter_game(callback: CallbackQuery, state: FSMContext):
    await run_filtered_search(callback.message, callback.from_user.id, state)
    await callback.answer()


@router.callback_query(F.data == "filter:role")
async def filter_role(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterForm.role)
    await callback.message.edit_text(
        "👤 <b>Выбери роль</b>\n\nКакую роль ищешь?",
        parse_mode="HTML",
        reply_markup=filter_roles_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter:role_set:"))
async def filter_role_set(callback: CallbackQuery, state: FSMContext):
    role = callback.data.split(":")[2]
    if role == "any":
        role = None

    await state.update_data(filter_role=role)
    await state.set_state(FilterForm.main)

    data = await state.get_data()
    await callback.message.edit_text(
        build_filter_summary(data),
        parse_mode="HTML",
        reply_markup=filter_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "filter:time")
async def filter_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterForm.time)
    await callback.message.edit_text(
        "🕐 <b>Выбери время</b>\n\nКогда ты обычно играешь?",
        parse_mode="HTML",
        reply_markup=filter_time_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter:time_set:"))
async def filter_time_set(callback: CallbackQuery, state: FSMContext):
    time_val = callback.data.split(":")[2]
    if time_val == "any":
        time_val = None

    await state.update_data(filter_time=time_val)
    await state.set_state(FilterForm.main)

    data = await state.get_data()
    await callback.message.edit_text(
        build_filter_summary(data),
        parse_mode="HTML",
        reply_markup=filter_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "filter:rating")
async def filter_rating(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterForm.rating)
    await callback.message.edit_text(
        "⭐ <b>Минимальный рейтинг</b>\n\nПоказывать только игроков с рейтингом:",
        parse_mode="HTML",
        reply_markup=filter_rating_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter:rating_set:"))
async def filter_rating_set(callback: CallbackQuery, state: FSMContext):
    rating_val = callback.data.split(":")[2]
    if rating_val == "any":
        rating_val = None
    else:
        rating_val = float(rating_val)

    await state.update_data(filter_rating=rating_val)
    await state.set_state(FilterForm.main)

    data = await state.get_data()
    await callback.message.edit_text(
        build_filter_summary(data),
        parse_mode="HTML",
        reply_markup=filter_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "filter:no_toxic")
async def filter_no_toxic(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = data.get("filter_no_toxic", False)
    await state.update_data(filter_no_toxic=not current)

    data = await state.get_data()
    await callback.message.edit_text(
        build_filter_summary(data),
        parse_mode="HTML",
        reply_markup=filter_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "filter:all")
async def filter_all(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterForm.all)
    data = await state.get_data()
    await callback.message.edit_text(
        "🔍 <b>Все фильтры</b>\n\n"
        + build_filter_summary(data)
        + "\n\nНастрой каждый фильтр и нажми «🔍 Искать»:",
        parse_mode="HTML",
        reply_markup=filter_summary_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "filter:search")
async def filter_search(callback: CallbackQuery, state: FSMContext):
    await run_filtered_search(callback.message, callback.from_user.id, state)
    await callback.answer()


async def run_filtered_search(message: Message, user_id: int, state: FSMContext):
    data = await state.get_data()

    game = data.get("filter_game")
    rank = data.get("filter_rank")
    role = data.get("filter_role")
    time_val = data.get("filter_time")
    rating = data.get("filter_rating")
    no_toxic = data.get("filter_no_toxic", False)

    log_event(user_id, "find", f"{game}|{rank}|{role}|{time_val}|{rating}")

    partners = find_partner_filtered(
        user_id=user_id,
        game=game,
        rank=rank,
        role=role,
        time=time_val,
        min_rating=rating,
        exclude_toxic=no_toxic,
        limit=5
    )

    if not partners:
        try:
            await message.edit_text(
                "😔 <b>Напарников не найдено</b>\n\n"
                "Попробуй ослабить фильтры или зайти позже.",
                parse_mode="HTML",
                reply_markup=filter_results_menu()
            )
        except Exception:
            await message.answer(
                "😔 <b>Напарников не найдено</b>\n\n"
                "Попробуй ослабить фильтры или зайти позже.",
                parse_mode="HTML",
                reply_markup=filter_results_menu()
            )
        await state.clear()
        return

    text = f"🔍 <b>Найдено напарников: {len(partners)}</b>\n\n"

    for p in partners:
        uid, username, p_game, p_rank, p_role, p_time, p_rating = p
        text += (
            f"👤 @{username or 'без имени'}\n"
            f"🎮 {p_game} | 🏆 {p_rank}\n"
            f"🎯 {p_role} | 🕐 {p_time}\n"
            f"⭐ {p_rating}/10\n"
            f"Написать: /msg_{uid}\n\n"
        )

    try:
        await message.edit_text(text, parse_mode="HTML", reply_markup=filter_results_menu())
    except Exception:
        await message.delete()
        await message.answer(text, parse_mode="HTML", reply_markup=filter_results_menu())

    await state.clear()


# ===== ЧАТ =====

@router.message(F.text.startswith("/msg_"))
async def cmd_msg(message: Message, state: FSMContext):
    try:
        to_user_id = int(message.text.replace("/msg_", ""))
    except ValueError:
        await message.answer("Ошибка. Попробуй снова.")
        return

    if to_user_id == message.from_user.id:
        await message.answer("❌ Нельзя писать самому себе.")
        return

    recipient = get_profile(to_user_id)
    if not recipient:
        await message.answer("❌ Пользователь не найден.")
        return

    recipient_name = recipient[1] or "игрок"

    await state.set_state(ChatForm.message)
    await state.update_data(to_user_id=to_user_id, recipient_name=recipient_name)

    await message.answer(
        f"✍️ Напиши сообщение для @{recipient_name}.\n\n"
        f"Отправь текст одним сообщением.\n"
        f"Отмена: /cancel"
    )


@router.message(ChatForm.message, ~F.text.startswith("/"))
async def process_message(message: Message, state: FSMContext):
    data = await state.get_data()
    to_user_id = data["to_user_id"]
    recipient_name = data["recipient_name"]

    text = message.text

    if len(text) > 1000:
        await message.answer("❌ Сообщение слишком длинное (макс. 1000 символов).")
        return

    save_message(message.from_user.id, to_user_id, text)
    log_event(message.from_user.id, "message_sent", f"to:{to_user_id}")

    sender_name = message.from_user.username or message.from_user.first_name

    try:
        await message.bot.send_message(
            chat_id=to_user_id,
            text=(
                f"💬 <b>Сообщение от @{sender_name}</b>\n\n"
                f"{text}\n\n"
                f"<i>Ответить: /reply</i>\n"
                f"<i>Написать: /msg_{message.from_user.id}</i>"
            ),
            parse_mode="HTML"
        )
        await message.answer(f"✅ Сообщение отправлено @{recipient_name}.")
    except Exception as e:
        await message.answer(
            f"⚠️ Сообщение сохранено, но не доставлено.\n"
            f"Возможно, пользователь заблокировал бота.\n\n"
            f"Ошибка: {str(e)[:100]}"
        )

    await state.clear()


@router.message(Command("inbox"))
async def cmd_inbox(message: Message):
    update_last_seen(message.from_user.id)
    messages = get_inbox(message.from_user.id, limit=10)

    if not messages:
        await message.answer("📭 Входящих сообщений нет.")
        return

    text = "📬 <b>Входящие сообщения</b>\n\n"

    for msg_id, from_user_id, username, msg_text, created_at, is_read in messages:
        status = "" if is_read else "🆕 "
        preview = msg_text[:50] + ("..." if len(msg_text) > 50 else "")
        text += f"{status}👤 @{username or from_user_id}\n"
        text += f"   {preview}\n"
        text += f"   <i>{created_at}</i>\n"
        text += f"   Ответить: /msg_{from_user_id}\n\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📬 Входящие")
async def cmd_inbox_button(message: Message):
    await cmd_inbox(message)


@router.message(Command("reply"))
async def cmd_reply(message: Message, state: FSMContext):
    last_sender = get_last_sender(message.from_user.id)

    if not last_sender:
        await message.answer("📭 Нет сообщений для ответа.")
        return

    sender = get_profile(last_sender)
    sender_name = sender[1] if sender else str(last_sender)

    await state.set_state(ChatForm.reply)
    await state.update_data(to_user_id=last_sender, recipient_name=sender_name)

    await message.answer(
        f"✍️ Ответь @{sender_name}.\n\n"
        f"Отправь текст одним сообщением.\n"
        f"Отмена: /cancel"
    )


@router.message(ChatForm.reply, ~F.text.startswith("/"))
async def process_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    to_user_id = data["to_user_id"]
    recipient_name = data["recipient_name"]

    text = message.text

    if len(text) > 1000:
        await message.answer("❌ Сообщение слишком длинное (макс. 1000 символов).")
        return

    save_message(message.from_user.id, to_user_id, text)
    log_event(message.from_user.id, "message_sent", f"to:{to_user_id}")

    sender_name = message.from_user.username or message.from_user.first_name

    try:
        await message.bot.send_message(
            chat_id=to_user_id,
            text=(
                f"💬 <b>Ответ от @{sender_name}</b>\n\n"
                f"{text}\n\n"
                f"<i>Ответить: /reply</i>"
            ),
            parse_mode="HTML"
        )
        await message.answer(f"✅ Ответ отправлен @{recipient_name}.")
    except Exception as e:
        await message.answer(
            f"⚠️ Сообщение сохранено, но не доставлено.\n"
            f"Ошибка: {str(e)[:100]}"
        )

    await state.clear()


@router.message(Command("chat"))
async def cmd_chat(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "Использование: <code>/chat &lt;user_id&gt;</code>\n"
            "Например: <code>/chat 123456789</code>",
            parse_mode="HTML"
        )
        return

    try:
        other_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    messages = get_conversation(message.from_user.id, other_id, limit=20)

    if not messages:
        await message.answer(f"📭 Диалога с {other_id} нет.")
        return

    other = get_profile(other_id)
    other_name = other[1] if other else str(other_id)

    text = f"💬 <b>Диалог с @{other_name}</b>\n\n"

    for from_id, msg_text, created_at in messages:
        if from_id == message.from_user.id:
            text += f"➡️ <b>Ты:</b> {msg_text}\n"
        else:
            text += f"⬅️ <b>@{other_name}:</b> {msg_text}\n"
        text += f"   <i>{created_at}</i>\n\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("unread"))
async def cmd_unread(message: Message):
    count = count_unread(message.from_user.id)

    if count == 0:
        await message.answer("📭 Непрочитанных сообщений нет.")
    else:
        await message.answer(f"📬 Непрочитанных сообщений: <b>{count}</b>", parse_mode="HTML")

# ===== ОЦЕНКА НАПАРНИКА =====

@router.message(Command("rate"))
async def cmd_rate(message: Message, state: FSMContext):
    """Начинает процесс оценки напарника."""
    parts = message.text.split()

    if len(parts) < 2:
        await message.answer(
            "⭐ <b>Оценка напарника</b>\n\n"
            "Использование: <code>/rate &lt;user_id&gt;</code>\n\n"
            "Например: <code>/rate 123456789</code>\n\n"
            "Где взять ID? Смотри в /find или /inbox — там указан ID напарника.",
            parse_mode="HTML"
        )
        return

    try:
        to_user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    if to_user_id == message.from_user.id:
        await message.answer("❌ Нельзя оценивать себя.")
        return

    # Проверяем, что пользователь существует
    target = get_profile(to_user_id)
    if not target:
        await message.answer("❌ Пользователь не найден.")
        return

    # Проверяем, не оценивал ли уже сегодня
    if has_rated_today(message.from_user.id, to_user_id):
        await message.answer(
            f"⚠️ Ты уже оценивал @{target[1]} сегодня.\n"
            "Можно оценивать одного игрока раз в день."
        )
        return

    target_name = target[1] or str(to_user_id)

    await state.set_state(RatingForm.stars)
    await state.update_data(to_user_id=to_user_id, tags=[])

    await message.answer(
        f"⭐ <b>Оценка @{target_name}</b>\n\n"
        f"Сколько звёзд?",
        parse_mode="HTML",
        reply_markup=rating_stars_menu(to_user_id)
    )


@router.callback_query(F.data == "rating:cancel")
async def rating_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Оценка отменена.")
    await callback.answer()


@router.callback_query(F.data == "rating:menu")
async def rating_menu_back(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Главное меню.", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data.startswith("rating:stars:"))
async def rating_stars(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    stars = int(parts[2])
    to_user_id = int(parts[3])

    await state.update_data(stars=stars, to_user_id=to_user_id, tags=[])
    await state.set_state(RatingForm.tags)

    target = get_profile(to_user_id)
    target_name = target[1] if target else str(to_user_id)

    stars_str = "⭐" * stars

    await callback.message.edit_text(
        f"⭐ <b>Оценка @{target_name}</b>\n\n"
        f"Звёзды: {stars_str}\n\n"
        f"Выбери теги (можно несколько):",
        parse_mode="HTML",
        reply_markup=rating_tags_menu(to_user_id, stars, [])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rating:tag_toggle:"))
async def rating_tag_toggle(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    tag = parts[2]
    to_user_id = int(parts[3])
    stars = int(parts[4])

    data = await state.get_data()
    tags = data.get("tags", [])

    if tag in tags:
        tags.remove(tag)
    else:
        tags.append(tag)

    await state.update_data(tags=tags)

    target = get_profile(to_user_id)
    target_name = target[1] if target else str(to_user_id)

    stars_str = "⭐" * stars
    tags_str = ", ".join(tags) if tags else "не выбрано"

    await callback.message.edit_text(
        f"⭐ <b>Оценка @{target_name}</b>\n\n"
        f"Звёзды: {stars_str}\n"
        f"Теги: {tags_str}\n\n"
        f"Выбери теги (можно несколько):",
        parse_mode="HTML",
        reply_markup=rating_tags_menu(to_user_id, stars, tags)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rating:back:"))
async def rating_back(callback: CallbackQuery, state: FSMContext):
    to_user_id = int(callback.data.split(":")[2])

    await state.set_state(RatingForm.stars)
    await state.update_data(to_user_id=to_user_id, tags=[])

    target = get_profile(to_user_id)
    target_name = target[1] if target else str(to_user_id)

    await callback.message.edit_text(
        f"⭐ <b>Оценка @{target_name}</b>\n\n"
        f"Сколько звёзд?",
        parse_mode="HTML",
        reply_markup=rating_stars_menu(to_user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rating:save:"))
async def rating_save(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    to_user_id = int(parts[2])
    stars = int(parts[3])

    data = await state.get_data()
    tags = data.get("tags", [])
    tags_str = ",".join(tags)

    # Сохраняем оценку
    success = add_rating_v2(
        from_user_id=callback.from_user.id,
        to_user_id=to_user_id,
        stars=stars,
        tags=tags_str,
    )

    if not success:
        await callback.answer("⚠️ Ты уже оценивал этого игрока сегодня.", show_alert=True)
        await state.clear()
        return

    # Пересчитываем рейтинг
    new_rating = recalculate_rating(to_user_id)

    # Логируем
    log_event(callback.from_user.id, "rating_given", f"to:{to_user_id}|stars:{stars}|tags:{tags_str}")

    # Уведомляем получателя
    try:
        tags_display = ", ".join(tags) if tags else "без тегов"
        stars_str = "⭐" * stars

        await callback.bot.send_message(
            chat_id=to_user_id,
            text=(
                f"⭐ <b>Тебя оценили!</b>\n\n"
                f"Оценка: {stars_str} ({stars}/5)\n"
                f"Теги: {tags_display}\n\n"
                f"Твой новый рейтинг: <b>{new_rating}/10</b>"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Не удалось уведомить {to_user_id}: {e}")

    await state.clear()

    target = get_profile(to_user_id)
    target_name = target[1] if target else str(to_user_id)

    await callback.message.edit_text(
        f"✅ <b>Спасибо за оценку!</b>\n\n"
        f"Ты оценил @{target_name}:\n"
        f"⭐ {stars}/5\n"
        f"🏷 {', '.join(tags) if tags else 'без тегов'}\n\n"
        f"Новый рейтинг: <b>{new_rating}/10</b>",
        parse_mode="HTML",
        reply_markup=rating_done_menu()
    )
    await callback.answer("✅ Оценка сохранена")


# ===== СТАТИСТИКА ОЦЕНОК =====

@router.message(Command("my_rating"))
async def cmd_my_rating(message: Message):
    """Показывает статистику оценок пользователя."""
    update_last_seen(message.from_user.id)

    stats = get_user_rating_stats(message.from_user.id)

    if stats["total_ratings"] == 0:
        await message.answer(
            "📭 Тебя ещё не оценивали.\n\n"
            "Играй с напарниками и проси их оценить тебя через /rate."
        )
        return

    user = get_profile(message.from_user.id)
    rating = user[6] if user else 5.0

    text = f"⭐ <b>Твоя статистика оценок</b>\n\n"
    text += f"Средняя оценка: <b>{stats['avg_stars']}/5</b>\n"
    text += f"Текущий рейтинг: <b>{rating}/10</b>\n"
    text += f"Всего оценок: <b>{stats['total_ratings']}</b>\n\n"

    if stats["distribution"]:
        text += "📊 <b>Распределение:</b>\n"
        for stars, count in stats["distribution"]:
            text += f"  {'⭐' * stars} — {count}\n"
        text += "\n"

    if stats["top_tags"]:
        text += "🏷 <b>Топ теги:</b>\n"
        for tag, count in stats["top_tags"]:
            text += f"  {tag} — {count}\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("recent_ratings"))
async def cmd_recent_ratings(message: Message):
    """Показывает последние оценки пользователя."""
    update_last_seen(message.from_user.id)

    ratings = get_user_ratings(message.from_user.id, limit=10)

    if not ratings:
        await message.answer("📭 Тебя ещё не оценивали.")
        return

    text = "⭐ <b>Последние оценки</b>\n\n"

    for stars, tags, comment, created_at, from_username in ratings:
        stars_str = "⭐" * stars
        tags_str = f" | {tags}" if tags else ""
        text += f"{stars_str} от @{from_username or 'аноним'}{tags_str}\n"
        text += f"   <i>{created_at}</i>\n\n"

    await message.answer(text, parse_mode="HTML")