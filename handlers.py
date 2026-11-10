from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    add_user, update_profile, get_profile, find_partner, add_rating,
    log_event, update_last_seen,
    save_message, get_inbox, get_conversation, mark_as_read,
    count_unread, count_unread_from, get_last_sender,
    delete_conversation, search_messages, count_messages_last_hour,
    block_user, unblock_user, is_blocked, get_blocked_users,
    find_partner_filtered_v2,
    add_rating_v2, get_user_ratings, get_user_rating_stats,
    has_rated_today, recalculate_rating,
    add_report, get_user_reports, get_user_reports_count,
    check_and_hide_user, is_user_hidden,
    get_game_ranks, get_game_roles,
    get_user_age_days, is_profile_filled, has_interaction,
    add_match, anti_fraud_check_v1,
    schedule_notification, check_mutual_match, has_notified_mutual,
    anti_fraud_check_v2, add_rating_v2_weighted, recalculate_rating_weighted,
    add_mentor, get_mentor, is_mentor, remove_mentor,
    find_mentors, add_mentor_review, get_mentor_rating,
    get_mentor_reviews, increment_mentor_sessions, recalculate_mentor_rating,
    init_mentors
)
from keyboards import (
    main_menu, games_menu, ranks_menu, roles_menu, time_menu, rating_menu,
    filter_main_menu, filter_roles_menu, filter_time_menu,
    filter_rating_menu, filter_results_menu, filter_summary_menu,
    rating_stars_menu, rating_tags_menu, rating_done_menu,
    report_reasons_menu, report_confirm_menu, report_done_menu,
    inbox_menu, chat_actions_menu, block_confirm_menu,
    unblock_menu, delete_confirm_menu, blocked_list_menu,
    developer_menu,
    style_menu, goal_menu, voice_menu, experience_menu,
    filter_style_menu, filter_goal_menu, filter_voice_menu, filter_experience_menu,
    mentor_menu, mentor_find_menu, mentor_review_menu, mentor_actions_menu,
    mentor_games_menu, mentor_roles_menu, mentor_time_menu
)

router = Router()


class ProfileForm(StatesGroup):
    game = State()
    rank = State()
    role = State()
    time = State()
    style = State()
    goal = State()
    voice = State()
    experience = State()


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


class MentorForm(StatesGroup):
    games = State()
    roles = State()
    time = State()
    description = State()


# ===== ОСНОВНЫЕ КОМАНДЫ =====

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

    if not is_profile_filled(message.from_user.id):
        schedule_notification(
            user_id=message.from_user.id,
            notification_type="profile_reminder",
            delay_seconds=24 * 3600
        )

    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я помогу найти напарника для игр.\n\n"
        "📋 <b>Команды:</b>\n"
        "/profile — заполнить профиль\n"
        "/find — найти напарника\n"
        "/me — твой профиль\n"
        "/rate &lt;id&gt; — оценить напарника\n"
        "/report &lt;id&gt; — пожаловаться\n"
        "/mentor — режим Ментора\n"
        "/my_rating — твоя статистика\n"
        "/inbox — входящие\n"
        "/help — все команды\n"
        "/cancel — отмена",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 <b>Все команды</b>\n\n"
        "<b>Профиль:</b>\n"
        "/profile — заполнить профиль\n"
        "/me — посмотреть профиль\n\n"
        "<b>Поиск:</b>\n"
        "/find — найти напарника с фильтрами\n\n"
        "<b>Чат:</b>\n"
        "/inbox — входящие\n"
        "/reply — ответить последнему\n"
        "/chat &lt;id&gt; — диалог\n"
        "/unread — непрочитанные\n"
        "/search &lt;текст&gt; — поиск по сообщениям\n"
        "/delete_chat &lt;id&gt; — удалить диалог\n"
        "/block &lt;id&gt; — заблокировать\n"
        "/unblock &lt;id&gt; — разблокировать\n"
        "/blocked — список заблокированных\n\n"
        "<b>Оценка:</b>\n"
        "/rate &lt;id&gt; — оценить напарника\n"
        "/my_rating — статистика оценок\n"
        "/recent_ratings — последние оценки\n\n"
        "<b>Жалобы:</b>\n"
        "/report &lt;id&gt; — пожаловаться\n"
        "/my_reports — жалобы на тебя\n\n"
        "<b>Ментор:</b>\n"
        "/mentor — режим Ментора\n\n"
        "<b>О проекте:</b>\n"
        "/developer — о разработчике",
        parse_mode="HTML",
        reply_markup=main_menu()
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

    ranks = get_game_ranks(game_name)

    if ranks:
        await state.set_state(ProfileForm.rank)
        await message.answer(
            f"🎮 {game_name}\n\nВыбери свой ранг:",
            reply_markup=ranks_menu(game_name)
        )
    else:
        await state.set_state(ProfileForm.rank)
        await message.answer(
            f"🎮 {game_name}\n\nНапиши свой ранг (вручную):"
        )


@router.message(ProfileForm.rank, ~F.text.startswith("/"))
async def process_rank(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.set_state(ProfileForm.game)
        await message.answer("Выбери игру:", reply_markup=games_menu())
        return

    await state.update_data(rank=message.text)

    data = await state.get_data()
    game_name = data.get("game", "")

    roles = get_game_roles(game_name)

    if roles:
        await state.set_state(ProfileForm.role)
        await message.answer(
            "Выбери свою роль:",
            reply_markup=roles_menu(game_name)
        )
    else:
        await state.set_state(ProfileForm.role)
        await message.answer("Напиши свою роль:")


@router.message(ProfileForm.role, ~F.text.startswith("/"))
async def process_role(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        data = await state.get_data()
        game_name = data.get("game", "")

        await state.set_state(ProfileForm.rank)

        ranks = get_game_ranks(game_name)
        if ranks:
            await message.answer(
                "Выбери свой ранг:",
                reply_markup=ranks_menu(game_name)
            )
        else:
            await message.answer("Напиши свой ранг:")
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

    await state.set_state(ProfileForm.style)
    await message.answer(
        "🔥 Какой у тебя стиль игры?",
        reply_markup=style_menu()
    )


@router.message(ProfileForm.style, ~F.text.startswith("/"))
async def process_style(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.set_state(ProfileForm.time)
        await message.answer("Когда обычно играешь?", reply_markup=time_menu())
        return

    await state.update_data(style=message.text)

    await state.set_state(ProfileForm.goal)
    await message.answer(
        "🎯 Какая у тебя цель в играх?",
        reply_markup=goal_menu()
    )


@router.message(ProfileForm.goal, ~F.text.startswith("/"))
async def process_goal(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.set_state(ProfileForm.style)
        await message.answer("Какой у тебя стиль игры?", reply_markup=style_menu())
        return

    await state.update_data(goal=message.text)

    await state.set_state(ProfileForm.voice)
    await message.answer(
        "🎤 Готов ли говорить голосом?",
        reply_markup=voice_menu()
    )


@router.message(ProfileForm.voice, ~F.text.startswith("/"))
async def process_voice(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.set_state(ProfileForm.goal)
        await message.answer("Какая у тебя цель?", reply_markup=goal_menu())
        return

    await state.update_data(voice=message.text)

    await state.set_state(ProfileForm.experience)
    await message.answer(
        "📊 Какой у тебя опыт?",
        reply_markup=experience_menu()
    )


@router.message(ProfileForm.experience, ~F.text.startswith("/"))
async def process_experience(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.set_state(ProfileForm.voice)
        await message.answer("Готов ли говорить голосом?", reply_markup=voice_menu())
        return

    await state.update_data(experience=message.text)

    data = await state.get_data()
    update_profile(
        message.from_user.id,
        data["game"], data["rank"], data["role"], data["time"],
        data.get("style"), data.get("goal"), data.get("voice"), data.get("experience")
    )
    log_event(message.from_user.id, "profile_update", data["game"])
    update_last_seen(message.from_user.id)

    await state.clear()
    await message.answer(
        f"✅ Профиль сохранён!\n\n"
        f"🎮 Игра: {data['game']}\n"
        f"🏆 Ранг: {data['rank']}\n"
        f"🎯 Роль: {data['role']}\n"
        f"🕐 Время: {data['time']}\n"
        f"🔥 Стиль: {data.get('style', '—')}\n"
        f"🎯 Цель: {data.get('goal', '—')}\n"
        f"🎤 Голос: {data.get('voice', '—')}\n"
        f"📊 Опыт: {data.get('experience', '—')}",
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

    user_id = user[0]
    username = user[1]
    game = user[2]
    rank = user[3]
    role = user[4]
    time = user[5]
    style = user[6] if len(user) > 6 else None
    goal = user[7] if len(user) > 7 else None
    voice = user[8] if len(user) > 8 else None
    experience = user[9] if len(user) > 9 else None

    # ===== ПРАВИЛЬНОЕ ПОЛУЧЕНИЕ РЕЙТИНГА И БОНУСА =====
    from database import get_user_rating, get_user_bonus
    rating = get_user_rating(message.from_user.id) or 5.0
    bonus = get_user_bonus(message.from_user.id) or 0.0
    # ===== /ПОЛУЧЕНИЕ =====

    # Показываем бонус, только если он есть
    bonus_str = f"🎁 Бонус: {bonus}" if bonus > 0 else ""

    text = (
        f"👤 Твой профиль:\n\n"
        f"🎮 Игра: {game}\n"
        f"🏆 Ранг: {rank}\n"
        f"🎯 Роль: {role}\n"
        f"🕐 Время: {time}\n"
        f"🔥 Стиль: {style or '—'}\n"
        f"🎯 Цель: {goal or '—'}\n"
        f"🎤 Голос: {voice or '—'}\n"
        f"📊 Опыт: {experience or '—'}\n"
        f"⭐ Рейтинг: {rating}/10"
    )

    if bonus_str:
        text += f"\n{bonus_str}"

    await message.answer(text)

# ===== О РАЗРАБОТЧИКЕ =====

@router.message(F.text == "👨‍💻 О разработчике")
@router.message(Command("developer"))
async def cmd_developer(message: Message):
    update_last_seen(message.from_user.id)

    text = (
        "👨‍💻 <b>О разработчике</b>\n\n"
        "Привет! Я создатель <b>DuoFinder</b> — бота для поиска напарников в играх.\n\n"
        "Моя цель — сделать так, чтобы каждый геймер нашёл своего напарника: "
        "не просто «тело для катки», а человека, с которым комфортно и результативно играть.\n\n"
        "🔗 <b>Мои соцсети:</b>\n"
        "• Twitch — стримы и игры\n"
        "• YouTube — видео о разработке\n"
        "• Instagram — за кулисами\n"
        "• TikTok — короткие ролики\n\n"
        "💖 <b>Поддержать проект:</b>\n"
        "Если тебе нравится бот — можешь поддержать разработку. "
        "Любая сумма помогает делать проект лучше.\n\n"
        "Спасибо, что ты со мной! 🙏"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=developer_menu()
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
        filter_style=None,
        filter_goal=None,
        filter_voice=None,
        filter_experience=None,
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

    style = data.get("filter_style") or "любой"
    goal = data.get("filter_goal") or "любая"
    voice = data.get("filter_voice") or "любой"
    experience = data.get("filter_experience") or "любой"

    return (
        f"🔍 <b>Фильтры поиска</b>\n\n"
        f"🎮 Игра: <b>{game}</b>\n"
        f"🏆 Ранг: <b>{rank}</b>\n"
        f"👤 Роль: {role}\n"
        f"🕐 Время: {time}\n"
        f"⭐ Рейтинг: {rating_str}\n"
        f"🔥 Стиль: {style}\n"
        f"🎯 Цель: {goal}\n"
        f"🎤 Голос: {voice}\n"
        f"📊 Опыт: {experience}\n"
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
    data["filter_style"] = None
    data["filter_goal"] = None
    data["filter_voice"] = None
    data["filter_experience"] = None
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

@router.callback_query(F.data == "filter:mentor")
async def filter_mentor(callback: CallbackQuery, state: FSMContext):
    """Краткое объяснение, кто такие менторы, и переход к поиску."""
    await callback.message.edit_text(
        "🎓 <b>Кто такие менторы?</b>\n\n"
        "Ментор — это <b>опытный игрок</b>, который готов помочь новичкам:\n"
        "• Объяснить механику игры\n"
        "• Показать роли и тактики\n"
        "• Сыграть вместе и подсказать\n\n"
        "<b>Требования к менторам:</b>\n"
        "• Рейтинг 9.8+\n"
        "• Заполненный профиль\n"
        "• Опыт в игре\n\n"
        "Если хочешь <b>стать ментором</b> — /mentor → «Стать ментором».\n\n"
        "Нажми «Продолжить», чтобы найти ментора.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔍 Продолжить", callback_data="mentor:find")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="filter:menu")],
            ]
        )
    )
    await callback.answer()

@router.callback_query(F.data == "filter:style")
async def filter_style(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterForm.all)
    await callback.message.edit_text(
        "🔥 <b>Стиль игры</b>\n\nКакой стиль ищешь?",
        parse_mode="HTML",
        reply_markup=filter_style_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter:style_set:"))
async def filter_style_set(callback: CallbackQuery, state: FSMContext):
    style_val = callback.data.split(":")[2]
    if style_val == "any":
        style_val = None

    await state.update_data(filter_style=style_val)
    data = await state.get_data()
    await callback.message.edit_text(
        build_filter_summary(data),
        parse_mode="HTML",
        reply_markup=filter_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "filter:goal")
async def filter_goal(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterForm.all)
    await callback.message.edit_text(
        "🎯 <b>Цель</b>\n\nКакая цель?",
        parse_mode="HTML",
        reply_markup=filter_goal_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter:goal_set:"))
async def filter_goal_set(callback: CallbackQuery, state: FSMContext):
    goal_val = callback.data.split(":")[2]
    if goal_val == "any":
        goal_val = None

    await state.update_data(filter_goal=goal_val)
    data = await state.get_data()
    await callback.message.edit_text(
        build_filter_summary(data),
        parse_mode="HTML",
        reply_markup=filter_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "filter:voice")
async def filter_voice(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterForm.all)
    await callback.message.edit_text(
        "🎤 <b>Голос</b>\n\nКакой голос?",
        parse_mode="HTML",
        reply_markup=filter_voice_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter:voice_set:"))
async def filter_voice_set(callback: CallbackQuery, state: FSMContext):
    voice_val = callback.data.split(":")[2]
    if voice_val == "any":
        voice_val = None

    await state.update_data(filter_voice=voice_val)
    data = await state.get_data()
    await callback.message.edit_text(
        build_filter_summary(data),
        parse_mode="HTML",
        reply_markup=filter_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "filter:experience")
async def filter_experience(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FilterForm.all)
    await callback.message.edit_text(
        "📊 <b>Опыт</b>\n\nКакой опыт?",
        parse_mode="HTML",
        reply_markup=filter_experience_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter:experience_set:"))
async def filter_experience_set(callback: CallbackQuery, state: FSMContext):
    exp_val = callback.data.split(":")[2]
    if exp_val == "any":
        exp_val = None

    await state.update_data(filter_experience=exp_val)
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
    style = data.get("filter_style")
    goal = data.get("filter_goal")
    voice = data.get("filter_voice")
    experience = data.get("filter_experience")

    log_event(user_id, "find", f"{game}|{rank}|{role}|{time_val}|{rating}|{style}|{goal}|{voice}|{experience}")

    partners = find_partner_filtered_v2(
        user_id=user_id,
        game=game,
        rank=rank,
        role=role,
        time=time_val,
        min_rating=rating,
        exclude_toxic=no_toxic,
        style=style,
        goal=goal,
        voice=voice,
        experience=experience,
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
        uid, username, p_game, p_rank, p_role, p_time, p_rating, p_style, p_goal, p_voice, p_exp = p
        text += (
            f"👤 @{username or 'без имени'}\n"
            f"🎮 {p_game} | 🏆 {p_rank}\n"
            f"🎯 {p_role} | 🕐 {p_time}\n"
            f"🔥 {p_style or '—'} | 🎯 {p_goal or '—'}\n"
            f"🎤 {p_voice or '—'} | 📊 {p_exp or '—'}\n"
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

    if is_blocked(to_user_id, message.from_user.id):
        await message.answer("❌ Пользователь заблокировал тебя.")
        return

    if is_blocked(message.from_user.id, to_user_id):
        await message.answer(
            "❌ Ты заблокировал этого пользователя.\n"
            f"Разблокировать: /unblock {to_user_id}"
        )
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

    text = message.text.strip()

    if not text:
        await message.answer("❌ Сообщение пустое.")
        return

    if len(text) > 1000:
        await message.answer("❌ Сообщение слишком длинное (макс. 1000 символов).")
        return

    msg_count = count_messages_last_hour(message.from_user.id)
    if msg_count >= 20:
        await message.answer(
            "⚠️ Ты отправил слишком много сообщений за последний час (лимит: 20).\n"
            "Попробуй позже."
        )
        await state.clear()
        return

    if is_blocked(to_user_id, message.from_user.id):
        await message.answer("❌ Пользователь заблокировал тебя.")
        await state.clear()
        return

    msg_id = save_message(message.from_user.id, to_user_id, text)

    add_match(message.from_user.id, to_user_id)

    if check_mutual_match(message.from_user.id, to_user_id):
        if not has_notified_mutual(message.from_user.id, to_user_id):
            schedule_notification(
                user_id=message.from_user.id,
                notification_type="mutual_match",
                data=f"{to_user_id}|{recipient_name}"
            )
            sender_name = message.from_user.username or message.from_user.first_name
            schedule_notification(
                user_id=to_user_id,
                notification_type="mutual_match",
                data=f"{message.from_user.id}|{sender_name}"
            )

    log_event(message.from_user.id, "message_sent", f"to:{to_user_id}")

    sender_name = message.from_user.username or message.from_user.first_name

    try:
        await message.bot.send_message(
            chat_id=to_user_id,
            text=(
                f"💬 <b>Сообщение от @{sender_name}</b>\n\n"
                f"{text}\n\n"
                f"<i>Ответить: /reply</i>\n"
                f"<i>Диалог: /chat {message.from_user.id}</i>"
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
        await message.answer(
            "📭 Входящих сообщений нет.",
            reply_markup=inbox_menu()
        )
        return

    text = "📬 <b>Входящие сообщения</b>\n\n"

    for from_user_id, username, msg_text, created_at, is_read, unread_count in messages:
        unread_mark = f"🔴 {unread_count}" if unread_count > 0 else ""
        preview = msg_text[:60] + ("..." if len(msg_text) > 60 else "")
        text += f"👤 @{username or from_user_id} {unread_mark}\n"
        text += f"   {preview}\n"
        text += f"   <i>{created_at}</i>\n"
        text += f"   /chat_{from_user_id}\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=inbox_menu())


@router.message(F.text == "📬 Входящие")
async def cmd_inbox_button(message: Message):
    await cmd_inbox(message)


@router.callback_query(F.data == "inbox:refresh")
async def callback_inbox_refresh(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_inbox(callback.message)
    await callback.answer("🔄 Обновлено")


@router.callback_query(F.data == "inbox:menu")
async def callback_inbox_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Главное меню.", reply_markup=main_menu())
    await callback.answer()


@router.message(F.text.startswith("/chat_"))
async def cmd_chat_short(message: Message):
    try:
        other_id = int(message.text.replace("/chat_", ""))
    except ValueError:
        await message.answer("Ошибка. Попробуй снова.")
        return

    await show_conversation(message, other_id)


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

    await show_conversation(message, other_id)


async def show_conversation(message: Message, other_id: int):
    messages = get_conversation(message.from_user.id, other_id, limit=30)

    mark_as_read(message.from_user.id, other_id)

    other = get_profile(other_id)
    other_name = other[1] if other else str(other_id)

    if not messages:
        await message.answer(
            f"💬 <b>Диалог с @{other_name}</b>\n\n"
            f"📭 Сообщений пока нет.\n\n"
            f"Написать: /msg_{other_id}",
            parse_mode="HTML",
            reply_markup=chat_actions_menu(other_id)
        )
        return

    text = f"💬 <b>Диалог с @{other_name}</b>\n\n"

    for msg_id, from_id, msg_text, reply_to_id, is_read, created_at in messages:
        if from_id == message.from_user.id:
            text += f"➡️ <b>Ты:</b> {msg_text}\n"
            if is_read:
                text += f"   ✅ <i>прочитано</i>\n"
            else:
                text += f"   ✓ <i>доставлено</i>\n"
        else:
            text += f"⬅️ <b>@{other_name}:</b> {msg_text}\n"

        text += f"   <i>{created_at}</i>\n\n"

    if len(text) > 4000:
        parts = []
        current = f"💬 <b>Диалог с @{other_name}</b>\n\n"

        for msg_id, from_id, msg_text, reply_to_id, is_read, created_at in messages:
            line = ""
            if from_id == message.from_user.id:
                line = f"➡️ <b>Ты:</b> {msg_text}\n"
            else:
                line = f"⬅️ <b>@{other_name}:</b> {msg_text}\n"
            line += f"   <i>{created_at}</i>\n\n"

            if len(current) + len(line) > 4000:
                parts.append(current)
                current = line
            else:
                current += line

        if current:
            parts.append(current)

        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                await message.answer(part, parse_mode="HTML", reply_markup=chat_actions_menu(other_id))
            else:
                await message.answer(part, parse_mode="HTML")
    else:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=chat_actions_menu(other_id)
        )


@router.message(Command("reply"))
async def cmd_reply(message: Message, state: FSMContext):
    last_sender = get_last_sender(message.from_user.id)

    if not last_sender:
        await message.answer("📭 Нет сообщений для ответа.")
        return

    if is_blocked(message.from_user.id, last_sender):
        await message.answer(
            "❌ Ты заблокировал этого пользователя.\n"
            f"Разблокировать: /unblock {last_sender}"
        )
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

    text = message.text.strip()

    if not text:
        await message.answer("❌ Сообщение пустое.")
        return

    if len(text) > 1000:
        await message.answer("❌ Сообщение слишком длинное (макс. 1000 символов).")
        return

    if is_blocked(to_user_id, message.from_user.id):
        await message.answer("❌ Пользователь заблокировал тебя.")
        await state.clear()
        return

    msg_id = save_message(message.from_user.id, to_user_id, text)

    add_match(message.from_user.id, to_user_id)

    if check_mutual_match(message.from_user.id, to_user_id):
        if not has_notified_mutual(message.from_user.id, to_user_id):
            schedule_notification(
                user_id=message.from_user.id,
                notification_type="mutual_match",
                data=f"{to_user_id}|{recipient_name}"
            )
            sender_name = message.from_user.username or message.from_user.first_name
            schedule_notification(
                user_id=to_user_id,
                notification_type="mutual_match",
                data=f"{message.from_user.id}|{sender_name}"
            )

    log_event(message.from_user.id, "message_sent", f"to:{to_user_id}")

    sender_name = message.from_user.username or message.from_user.first_name

    try:
        await message.bot.send_message(
            chat_id=to_user_id,
            text=(
                f"💬 <b>Ответ от @{sender_name}</b>\n\n"
                f"{text}\n\n"
                f"<i>Ответить: /reply</i>\n"
                f"<i>Диалог: /chat {message.from_user.id}</i>"
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


@router.message(Command("unread"))
async def cmd_unread(message: Message):
    count = count_unread(message.from_user.id)

    if count == 0:
        await message.answer("📭 Непрочитанных сообщений нет.")
    else:
        await message.answer(f"📬 Непрочитанных сообщений: <b>{count}</b>", parse_mode="HTML")


@router.message(Command("search"))
async def cmd_search(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Использование: <code>/search &lt;текст&gt;</code>\n"
            "Например: <code>/search привет</code>",
            parse_mode="HTML"
        )
        return

    query = parts[1]
    messages = search_messages(message.from_user.id, query, limit=20)

    if not messages:
        await message.answer(f"🔍 Ничего не найдено по запросу «{query}».")
        return

    text = f"🔍 <b>Найдено: {len(messages)}</b>\n\n"

    for msg_id, from_id, to_id, msg_text, created_at in messages:
        direction = "➡️" if from_id == message.from_user.id else "⬅️"
        preview = msg_text[:80] + ("..." if len(msg_text) > 80 else "")
        text += f"{direction} {preview}\n"
        text += f"   <i>{created_at}</i>\n\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("delete_chat"))
async def cmd_delete_chat(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "Использование: <code>/delete_chat &lt;user_id&gt;</code>",
            parse_mode="HTML"
        )
        return

    try:
        other_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    count = delete_conversation(message.from_user.id, other_id)

    if count == 0:
        await message.answer("📭 Диалог пуст.")
    else:
        await message.answer(f"🗑 Удалено сообщений: <b>{count}</b>", parse_mode="HTML")


@router.message(Command("block"))
async def cmd_block(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "Использование: <code>/block &lt;user_id&gt;</code>",
            parse_mode="HTML"
        )
        return

    try:
        other_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    if other_id == message.from_user.id:
        await message.answer("❌ Нельзя заблокировать себя.")
        return

    if is_blocked(message.from_user.id, other_id):
        await message.answer("⚠️ Пользователь уже заблокирован.")
        return

    block_user(message.from_user.id, other_id)
    log_event(message.from_user.id, "block_user", f"blocked:{other_id}")

    other = get_profile(other_id)
    other_name = other[1] if other else str(other_id)

    await message.answer(
        f"🚫 Пользователь @{other_name} заблокирован.\n\n"
        f"Он больше не сможет писать тебе.\n"
        f"Разблокировать: /unblock {other_id}"
    )


@router.message(Command("unblock"))
async def cmd_unblock(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "Использование: <code>/unblock &lt;user_id&gt;</code>",
            parse_mode="HTML"
        )
        return

    try:
        other_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    if unblock_user(message.from_user.id, other_id):
        await message.answer(f"✅ Пользователь {other_id} разблокирован.")
    else:
        await message.answer("⚠️ Пользователь не был заблокирован.")


@router.message(Command("blocked"))
async def cmd_blocked(message: Message):
    blocked = get_blocked_users(message.from_user.id)

    if not blocked:
        await message.answer(
            "📭 Ты никого не заблокировал.",
            reply_markup=blocked_list_menu()
        )
        return

    text = "🚫 <b>Заблокированные</b>\n\n"
    for blocked_id, username, created_at in blocked:
        text += f"👤 @{username or blocked_id}\n"
        text += f"   ID: <code>{blocked_id}</code>\n"
        text += f"   <i>{created_at}</i>\n"
        text += f"   Разблокировать: /unblock {blocked_id}\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=blocked_list_menu())


# ===== ИНЛАЙН-ДЕЙСТВИЯ В ДИАЛОГЕ =====

@router.callback_query(F.data.startswith("chat:write:"))
async def callback_chat_write(callback: CallbackQuery, state: FSMContext):
    other_id = int(callback.data.split(":")[2])

    other = get_profile(other_id)
    other_name = other[1] if other else str(other_id)

    await state.set_state(ChatForm.message)
    await state.update_data(to_user_id=other_id, recipient_name=other_name)

    await callback.message.edit_text(
        f"✍️ Напиши сообщение для @{other_name}.\n\n"
        f"Отправь текст одним сообщением.\n"
        f"Отмена: /cancel"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("chat:view:"))
async def callback_chat_view(callback: CallbackQuery):
    other_id = int(callback.data.split(":")[2])
    await callback.message.delete()
    await show_conversation(callback.message, other_id)
    await callback.answer()


@router.callback_query(F.data.startswith("chat:delete:"))
async def callback_chat_delete(callback: CallbackQuery):
    other_id = int(callback.data.split(":")[2])

    other = get_profile(other_id)
    other_name = other[1] if other else str(other_id)

    await callback.message.edit_text(
        f"🗑 <b>Удалить диалог с @{other_name}?</b>\n\n"
        f"Все сообщения будут удалены у тебя.\n"
        f"У собеседника — останутся.",
        parse_mode="HTML",
        reply_markup=delete_confirm_menu(other_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("chat:delete_confirm:"))
async def callback_delete_confirm(callback: CallbackQuery):
    other_id = int(callback.data.split(":")[2])

    count = delete_conversation(callback.from_user.id, other_id)

    await callback.message.edit_text(
        f"✅ Удалено сообщений: <b>{count}</b>",
        parse_mode="HTML"
    )
    await callback.answer("🗑 Диалог удалён")


@router.callback_query(F.data.startswith("chat:block:"))
async def callback_chat_block(callback: CallbackQuery):
    other_id = int(callback.data.split(":")[2])

    other = get_profile(other_id)
    other_name = other[1] if other else str(other_id)

    await callback.message.edit_text(
        f"🚫 <b>Заблокировать @{other_name}?</b>\n\n"
        f"Он не сможет писать тебе.",
        parse_mode="HTML",
        reply_markup=block_confirm_menu(other_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("chat:block_confirm:"))
async def callback_block_confirm(callback: CallbackQuery):
    other_id = int(callback.data.split(":")[2])

    if is_blocked(callback.from_user.id, other_id):
        await callback.answer("⚠️ Уже заблокирован", show_alert=True)
        return

    block_user(callback.from_user.id, other_id)
    log_event(callback.from_user.id, "block_user", f"blocked:{other_id}")

    other = get_profile(other_id)
    other_name = other[1] if other else str(other_id)

    await callback.message.edit_text(
        f"🚫 Пользователь @{other_name} заблокирован.\n\n"
        f"Разблокировать: /unblock {other_id}",
        parse_mode="HTML"
    )
    await callback.answer("🚫 Заблокирован")


@router.callback_query(F.data.startswith("chat:unblock:"))
async def callback_unblock(callback: CallbackQuery):
    other_id = int(callback.data.split(":")[2])

    unblock_user(callback.from_user.id, other_id)

    await callback.message.edit_text(
        f"✅ Пользователь {other_id} разблокирован."
    )
    await callback.answer("✅ Разблокирован")


@router.callback_query(F.data == "chat:menu")
async def callback_chat_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Главное меню.", reply_markup=main_menu())
    await callback.answer()


# ===== ОЦЕНКА НАПАРНИКА =====

@router.message(Command("rate"))
async def cmd_rate(message: Message, state: FSMContext):
    parts = message.text.split()

    if len(parts) < 2:
        await message.answer(
            "⭐ <b>Оценка напарника</b>\n\n"
            "Использование: <code>/rate &lt;user_id&gt;</code>\n\n"
            "Например: <code>/rate 123456789</code>",
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

    target = get_profile(to_user_id)
    if not target:
        await message.answer("❌ Пользователь не найден.")
        return

    check = anti_fraud_check_v1(message.from_user.id, to_user_id)

    if not check["allowed"]:
        target_name = target[1] or str(to_user_id)
        await message.answer(
            f"🚫 <b>Оценка недоступна</b>\n\n"
            f"Причина: {check['reason']}\n\n"
            f"<i>Это защита от накрутки рейтинга.</i>",
            parse_mode="HTML"
        )
        return

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

    # ===== АНТИФРОД. УРОВЕНЬ 2: расчёт веса =====
    fraud_check = anti_fraud_check_v2(callback.from_user.id)
    weight = fraud_check["weight"]
    flags = fraud_check["flags"]
    # ===== /АНТИФРОД =====

    success = add_rating_v2_weighted(
        from_user_id=callback.from_user.id,
        to_user_id=to_user_id,
        stars=stars,
        tags=tags_str,
        weight=weight,
    )

    if not success:
        await callback.answer("⚠️ Ты уже оценивал этого игрока сегодня.", show_alert=True)
        await state.clear()
        return

    new_rating = recalculate_rating_weighted(to_user_id)

    rater_name = callback.from_user.username or callback.from_user.first_name
    schedule_notification(
        user_id=to_user_id,
        notification_type="rate_reminder",
        data=f"{callback.from_user.id}|{rater_name}",
        delay_seconds=3600
    )

    log_event(
        callback.from_user.id,
        "rating_given",
        f"to:{to_user_id}|stars:{stars}|tags:{tags_str}|weight:{weight}"
    )

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

    # Информация о весе — только если вес снижен
    weight_info = ""
    if weight < 1.0:
        weight_info = (
            f"\n\n⚠️ <b>Вес оценки снижен: {weight}</b>\n"
            f"<i>Причина: {', '.join(flags)}</i>"
        )

    await callback.message.edit_text(
        f"✅ <b>Спасибо за оценку!</b>\n\n"
        f"Ты оценил @{target_name}:\n"
        f"⭐ {stars}/5\n"
        f"🏷 {', '.join(tags) if tags else 'без тегов'}\n\n"
        f"Новый рейтинг: <b>{new_rating}/10</b>"
        f"{weight_info}",
        parse_mode="HTML",
        reply_markup=rating_done_menu()
    )
    await callback.answer("✅ Оценка сохранена")


@router.message(Command("my_rating"))
async def cmd_my_rating(message: Message):
    update_last_seen(message.from_user.id)

    stats = get_user_rating_stats(message.from_user.id)

    if stats["total_ratings"] == 0:
        await message.answer(
            "📭 Тебя ещё не оценивали.\n\n"
            "Играй с напарниками и проси их оценить тебя через /rate."
        )
        return

    user = get_profile(message.from_user.id)
    rating = user[11] if user and len(user) > 11 else 5.0

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


# ===== ЖАЛОБЫ =====

@router.message(Command("report"))
async def cmd_report(message: Message, state: FSMContext):
    parts = message.text.split()

    if len(parts) < 2:
        await message.answer(
            "🚨 <b>Пожаловаться на игрока</b>\n\n"
            "Использование: <code>/report &lt;user_id&gt;</code>\n\n"
            "Например: <code>/report 123456789</code>",
            parse_mode="HTML"
        )
        return

    try:
        to_user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return

    if to_user_id == message.from_user.id:
        await message.answer("❌ Нельзя жаловаться на себя.")
        return

    target = get_profile(to_user_id)
    if not target:
        await message.answer("❌ Пользователь не найден.")
        return

    target_name = target[1] or str(to_user_id)

    await state.update_data(to_user_id=to_user_id, target_name=target_name)

    await message.answer(
        f"🚨 <b>Жалоба на @{target_name}</b>\n\n"
        f"Выбери причину:",
        parse_mode="HTML",
        reply_markup=report_reasons_menu(to_user_id)
    )


@router.callback_query(F.data == "report:cancel")
async def report_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Жалоба отменена.")
    await callback.answer()


@router.callback_query(F.data == "report:menu")
async def report_menu_back(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("Главное меню.", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data.startswith("report:reason:"))
async def report_reason(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    reason = parts[2]
    to_user_id = int(parts[3])

    data = await state.get_data()
    target_name = data.get("target_name", str(to_user_id))

    await callback.message.edit_text(
        f"🚨 <b>Подтверди жалобу</b>\n\n"
        f"Игрок: @{target_name}\n"
        f"Причина: <b>{reason}</b>\n\n"
        f"Жалоба будет отправлена админу.",
        parse_mode="HTML",
        reply_markup=report_confirm_menu(to_user_id, reason)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("report:back:"))
async def report_back(callback: CallbackQuery, state: FSMContext):
    to_user_id = int(callback.data.split(":")[2])

    data = await state.get_data()
    target_name = data.get("target_name", str(to_user_id))

    await callback.message.edit_text(
        f"🚨 <b>Жалоба на @{target_name}</b>\n\n"
        f"Выбери причину:",
        parse_mode="HTML",
        reply_markup=report_reasons_menu(to_user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("report:confirm:"))
async def report_confirm(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    reason = parts[2]
    to_user_id = int(parts[3])

    success = add_report(
        from_user_id=callback.from_user.id,
        to_user_id=to_user_id,
        reason=reason
    )

    if not success:
        await callback.answer(
            "⚠️ Ты уже жаловался на этого игрока за последние 24 часа.",
            show_alert=True
        )
        await state.clear()
        return

    log_event(callback.from_user.id, "report_sent", f"to:{to_user_id}|reason:{reason}")

    hidden = check_and_hide_user(to_user_id)
    count = get_user_reports_count(to_user_id, days=7)

    data = await state.get_data()
    target_name = data.get("target_name", str(to_user_id))

    text = f"✅ <b>Жалоба отправлена</b>\n\n"
    text += f"Игрок: @{target_name}\n"
    text += f"Причина: {reason}\n\n"

    if hidden:
        text += f"⚠️ Игрок скрыт из выдачи на 7 дней (3+ жалоб).\n"
        text += f"Рейтинг снижен на 2 балла.\n\n"
    else:
        text += f"Жалоб за 7 дней: <b>{count}</b>\n"

    text += "Спасибо, что помогаешь сделать сообщество чище!"

    await state.clear()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=report_done_menu()
    )
    await callback.answer("✅ Жалоба отправлена")


@router.message(Command("my_reports"))
async def cmd_my_reports(message: Message):
    update_last_seen(message.from_user.id)

    count = get_user_reports_count(message.from_user.id, days=7)

    if count == 0:
        await message.answer("✅ На тебя нет жалоб за последние 7 дней. Так держать!")
        return

    reports = get_user_reports(message.from_user.id, limit=10)

    text = f"🚨 <b>Жалобы на тебя</b>\n\n"
    text += f"За 7 дней: <b>{count}</b>\n\n"

    for reason, comment, created_at, from_username in reports:
        text += f"• {reason} — <i>{created_at}</i>\n"

    if count >= 3:
        text += "\n⚠️ <b>Внимание:</b> при 3+ жалобах профиль скрывается из выдачи."
        text += "\nПопробуй быть вежливее с напарниками."

    await message.answer(text, parse_mode="HTML")


# ===== МЕНТОР =====

@router.message(Command("mentor"))
async def cmd_mentor(message: Message):
    update_last_seen(message.from_user.id)

    mentor_status = "🎓 Ты ментор" if is_mentor(message.from_user.id) else "❌ Ты не ментор"

    from database import get_user_rating
    rating = get_user_rating(message.from_user.id) or 5.0

    await message.answer(
        f"🎓 <b>Режим Ментора</b>\n\n"
        f"Статус: {mentor_status}\n"
        f"⭐ Твой рейтинг: {rating}/10\n\n"
        f"<b>Требования для ментора:</b>\n"
        f"• Рейтинг 9.8+\n"
        f"• Заполненный профиль\n\n"
        f"Выбери действие:",
        parse_mode="HTML",
        reply_markup=mentor_menu()
    )


@router.callback_query(F.data == "mentor:menu")
async def callback_mentor_menu(callback: CallbackQuery):
    """Возврат в главное меню."""
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )
    await callback.answer()


# ===== СТАТЬ МЕНТОРОМ =====

@router.callback_query(F.data == "mentor:become")
async def callback_mentor_become(callback: CallbackQuery, state: FSMContext):
    if is_mentor(callback.from_user.id):
        await callback.answer("⚠️ Ты уже ментор", show_alert=True)
        return

    user = get_profile(callback.from_user.id)
    if not user or not user[2]:
        await callback.answer("⚠️ Сначала заполни профиль: /profile", show_alert=True)
        return

    from database import get_user_rating
    rating = get_user_rating(callback.from_user.id)
    if rating is None:
        rating = 5.0

    if rating < 9.8:
        await callback.answer(
            f"⚠️ Стать ментором можно только с рейтингом 9.8+\n"
            f"Твой рейтинг: {rating}/10",
            show_alert=True
        )
        return

    await state.set_state(MentorForm.games)
    await state.update_data(
        mentor_games=[],
        mentor_roles={},
        mentor_time=[],
    )

    await callback.message.edit_text(
        "🎓 <b>Стать ментором</b>\n\n"
        "Шаг 1/4: <b>Выбери игры</b>, в которых можешь быть ментором.\n\n"
        "Нажимай на игры, чтобы добавить/убрать.\n"
        "Когда выберешь все — нажми «✅ Готово».",
        parse_mode="HTML",
        reply_markup=mentor_games_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mentor_game_toggle:"))
async def callback_mentor_game_toggle(callback: CallbackQuery, state: FSMContext):
    game_name = callback.data.split(":", 1)[1]

    data = await state.get_data()
    selected = data.get("mentor_games", [])

    if game_name in selected:
        selected.remove(game_name)
    else:
        selected.append(game_name)

    await state.update_data(mentor_games=selected)

    await callback.message.edit_text(
        "🎓 <b>Стать ментором</b>\n\n"
        "Шаг 1/4: <b>Выбери игры</b>, в которых можешь быть ментором.\n\n"
        f"Выбрано: <b>{', '.join(selected) if selected else 'ничего'}</b>\n\n"
        "Нажимай на игры, чтобы добавить/убрать.\n"
        "Когда выберешь все — нажми «✅ Готово».",
        parse_mode="HTML",
        reply_markup=mentor_games_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "mentor_games_done")
async def callback_mentor_games_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("mentor_games", [])

    if not selected:
        await callback.answer("⚠️ Выбери хотя бы одну игру", show_alert=True)
        return

    first_game = selected[0]
    await state.update_data(
        mentor_current_game=first_game,
        mentor_games_queue=selected.copy(),
        mentor_roles={},
    )
    await state.set_state(MentorForm.roles)

    await callback.message.edit_text(
        f"🎓 <b>Стать ментором</b>\n\n"
        f"Шаг 2/4: <b>Выбери роли для {first_game}</b>.\n\n"
        f"Нажимай на роли, чтобы добавить/убрать.\n"
        f"Когда выберешь — нажми «✅ Готово».",
        parse_mode="HTML",
        reply_markup=mentor_roles_menu(first_game, [])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mentor_role_toggle:"))
async def callback_mentor_role_toggle(callback: CallbackQuery, state: FSMContext):
    role_name = callback.data.split(":", 1)[1]

    data = await state.get_data()
    current_game = data.get("mentor_current_game")
    roles_dict = data.get("mentor_roles", {})

    if current_game not in roles_dict:
        roles_dict[current_game] = []

    if role_name in roles_dict[current_game]:
        roles_dict[current_game].remove(role_name)
    else:
        roles_dict[current_game].append(role_name)

    await state.update_data(mentor_roles=roles_dict)

    selected = roles_dict.get(current_game, [])

    await callback.message.edit_text(
        f"🎓 <b>Стать ментором</b>\n\n"
        f"Шаг 2/4: <b>Выбери роли для {current_game}</b>.\n\n"
        f"Выбрано: <b>{', '.join(selected) if selected else 'ничего'}</b>\n\n"
        f"Нажимай на роли, чтобы добавить/убрать.\n"
        f"Когда выберешь — нажми «✅ Готово».",
        parse_mode="HTML",
        reply_markup=mentor_roles_menu(current_game, selected)
    )
    await callback.answer()


@router.callback_query(F.data == "mentor_roles_done")
async def callback_mentor_roles_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    queue = data.get("mentor_games_queue", [])
    roles_dict = data.get("mentor_roles", {})
    current_game = data.get("mentor_current_game")

    if current_game and not roles_dict.get(current_game):
        await callback.answer("⚠️ Выбери хотя бы одну роль для этой игры", show_alert=True)
        return

    if current_game in queue:
        queue.remove(current_game)

    if queue:
        next_game = queue[0]
        await state.update_data(
            mentor_current_game=next_game,
            mentor_games_queue=queue,
        )

        await callback.message.edit_text(
            f"🎓 <b>Стать ментором</b>\n\n"
            f"Шаг 2/4: <b>Выбери роли для {next_game}</b>.\n\n"
            f"Нажимай на роли, чтобы добавить/убрать.\n"
            f"Когда выберешь — нажми «✅ Готово».",
            parse_mode="HTML",
            reply_markup=mentor_roles_menu(next_game, roles_dict.get(next_game, []))
        )
    else:
        await state.set_state(MentorForm.time)

        await callback.message.edit_text(
            "🎓 <b>Стать ментором</b>\n\n"
            "Шаг 3/4: <b>Выбери время</b>, когда можешь помочь.\n\n"
            "Нажимай на время, чтобы добавить/убрать.\n"
            "Когда выберешь — нажми «✅ Готово».",
            parse_mode="HTML",
            reply_markup=mentor_time_menu()
        )

    await callback.answer()


@router.callback_query(F.data.startswith("mentor_time_toggle:"))
async def callback_mentor_time_toggle(callback: CallbackQuery, state: FSMContext):
    time_val = callback.data.split(":", 1)[1]

    data = await state.get_data()
    selected = data.get("mentor_time", [])

    if time_val in selected:
        selected.remove(time_val)
    else:
        selected.append(time_val)

    await state.update_data(mentor_time=selected)

    await callback.message.edit_text(
        "🎓 <b>Стать ментором</b>\n\n"
        "Шаг 3/4: <b>Выбери время</b>, когда можешь помочь.\n\n"
        f"Выбрано: <b>{', '.join(selected) if selected else 'ничего'}</b>\n\n"
        "Нажимай на время, чтобы добавить/убрать.\n"
        "Когда выберешь — нажми «✅ Готово».",
        parse_mode="HTML",
        reply_markup=mentor_time_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "mentor_time_done")
async def callback_mentor_time_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("mentor_time", [])

    if not selected:
        await callback.answer("⚠️ Выбери хотя бы одно время", show_alert=True)
        return

    await state.set_state(MentorForm.description)

    await callback.message.edit_text(
        "🎓 <b>Стать ментором</b>\n\n"
        "Шаг 4/4: <b>Описание</b>.\n\n"
        "Расскажи о себе кратко:\n"
        "• Опыт\n"
        "• Что можешь объяснить\n"
        "• Как проходят сессии\n\n"
        "Например: <code>Играю 5 лет, объясню механику фарма и ролей</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(MentorForm.description, ~F.text.startswith("/"))
async def process_mentor_description(message: Message, state: FSMContext):
    data = await state.get_data()

    games_list = data.get("mentor_games", [])
    roles_dict = data.get("mentor_roles", {})
    time_list = data.get("mentor_time", [])

    games_str = ", ".join(games_list)

    roles_parts = []
    for game, roles in roles_dict.items():
        if roles:
            roles_parts.append(f"{game}: {', '.join(roles)}")
    roles_str = "; ".join(roles_parts) if roles_parts else "все"

    time_str = ", ".join(time_list)

    success = add_mentor(
        user_id=message.from_user.id,
        games=games_str,
        roles=roles_str,
        time=time_str,
        description=message.text.strip()
    )

    await state.clear()

    if success:
        await message.answer(
            "✅ <b>Ты стал ментором!</b>\n\n"
            f"🎮 Игры: {games_str}\n"
            f"🎯 Роли: {roles_str}\n"
            f"🕐 Время: {time_str}\n"
            f"📝 Описание: {message.text.strip()}\n\n"
            f"Теперь новички могут найти тебя через /mentor.",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
    else:
        await message.answer("❌ Ошибка. Попробуй позже.", reply_markup=main_menu())


# ===== НАЙТИ МЕНТОРА =====

@router.callback_query(F.data == "mentor:find")
async def callback_mentor_find(callback: CallbackQuery, state: FSMContext):
    await state.update_data(
        mentor_game=None,
        mentor_role=None,
        mentor_time=None,
    )

    await callback.message.edit_text(
        "🔍 <b>Поиск ментора</b>\n\n"
        "Выбери фильтры или нажми «Искать»:",
        parse_mode="HTML",
        reply_markup=mentor_find_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mentor:filter:"))
async def callback_mentor_filter(callback: CallbackQuery, state: FSMContext):
    filter_type = callback.data.split(":")[2]

    if filter_type == "game":
        from keyboards import games_inline_menu
        await callback.message.edit_text(
            "🎮 <b>Выбери игру</b>",
            reply_markup=games_inline_menu()
        )
    elif filter_type == "role":
        await callback.message.edit_text(
            "🎯 <b>Выбери роль</b>",
            reply_markup=filter_roles_menu()
        )
    elif filter_type == "time":
        await callback.message.edit_text(
            "🕐 <b>Выбери время</b>",
            reply_markup=filter_time_menu()
        )

    await callback.answer()


@router.callback_query(F.data == "mentor:search")
async def callback_mentor_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    game = data.get("mentor_game")
    role = data.get("mentor_role")
    time_val = data.get("mentor_time")

    mentors = find_mentors(game=game, role=role, time=time_val, limit=5)

    if not mentors:
        await callback.message.edit_text(
            "😔 <b>Менторов не найдено</b>\n\n"
            "Попробуй ослабить фильтры.",
            parse_mode="HTML",
            reply_markup=mentor_find_menu()
        )
        await callback.answer()
        return

    text = f"🎓 <b>Найдено менторов: {len(mentors)}</b>\n\n"

    for m in mentors:
        uid, username, games, roles, time, description, rating, sessions = m
        display_name = f"@{username}" if username else f"ID: {uid}"
        text += (
            f"👤 {display_name}\n"
            f"🎮 {games}\n"
            f"🎯 {roles or '—'}\n"
            f"🕐 {time or '—'}\n"
            f"📝 {description[:100]}{'...' if len(description) > 100 else ''}\n"
            f"⭐ {rating}/10 | 📊 Сессий: {sessions}\n"
            f"✍️ /msg_{uid}\n\n"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=mentor_find_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mentor:view:"))
async def callback_mentor_view(callback: CallbackQuery):
    mentor_id = int(callback.data.split(":")[2])

    mentor = get_mentor(mentor_id)
    if not mentor:
        await callback.answer("❌ Ментор не найден", show_alert=True)
        return

    uid, games, roles, time, description, is_active, rating, sessions, created_at = mentor

    user = get_profile(mentor_id)
    username = user[1] if user else None
    display_name = f"@{username}" if username else f"ID: {uid}"

    text = (
        f"🎓 <b>Ментор: {display_name}</b>\n\n"
        f"🎮 Игры: {games}\n"
        f"🎯 Роли: {roles or '—'}\n"
        f"🕐 Время: {time or '—'}\n"
        f"📝 Описание: {description or '—'}\n\n"
        f"⭐ Рейтинг: {rating}/10\n"
        f"📊 Сессий: {sessions}\n\n"
        f"✍️ Написать: /msg_{uid}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=mentor_actions_menu(mentor_id)
    )
    await callback.answer()


# ===== ОЦЕНКА МЕНТОРА =====

@router.callback_query(F.data.startswith("mentor:rate:"))
async def callback_mentor_rate(callback: CallbackQuery):
    mentor_id = int(callback.data.split(":")[2])

    await callback.message.edit_text(
        f"⭐ <b>Оценка ментора</b>\n\n"
        f"Сколько звёзд?",
        parse_mode="HTML",
        reply_markup=mentor_review_menu(mentor_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mentor:review:"))
async def callback_mentor_review(callback: CallbackQuery):
    parts = callback.data.split(":")
    stars = int(parts[2])
    mentor_id = int(parts[3])

    # ===== АНТИФРОД УРОВЕНЬ 2: вес оценки =====
    fraud_check = anti_fraud_check_v2(callback.from_user.id)
    weight = fraud_check["weight"]
    flags = fraud_check["flags"]
    # ===== /АНТИФРОД =====

    success = add_mentor_review(
        mentor_id, callback.from_user.id, stars, weight=weight
    )

    if not success:
        await callback.answer("⚠️ Ты уже оценивал этого ментора сегодня.", show_alert=True)
        return

    new_rating = recalculate_mentor_rating(mentor_id)
    increment_mentor_sessions(mentor_id)

    weight_info = ""
    if weight < 1.0:
        weight_info = (
            f"\n\n⚠️ <b>Вес оценки снижен: {weight}</b>\n"
            f"<i>Причина: {', '.join(flags)}</i>"
        )

    await callback.message.edit_text(
        f"✅ <b>Спасибо за оценку!</b>\n\n"
        f"Ты оценил ментора на {stars}/5.\n"
        f"Новый рейтинг: <b>{new_rating}/10</b>"
        f"{weight_info}",
        parse_mode="HTML"
    )
    await callback.answer("✅ Оценка сохранена")


# ===== ОТЗЫВЫ МЕНТОРА =====

@router.callback_query(F.data.startswith("mentor:reviews:"))
async def callback_mentor_reviews(callback: CallbackQuery):
    mentor_id = int(callback.data.split(":")[2])

    reviews = get_mentor_reviews(mentor_id, limit=10)

    if not reviews:
        await callback.message.edit_text(
            "📭 <b>Отзывов пока нет</b>",
            parse_mode="HTML",
            reply_markup=mentor_actions_menu(mentor_id)
        )
        await callback.answer()
        return

    text = "📋 <b>Отзывы ментора</b>\n\n"

    for stars, comment, created_at, username in reviews:
        stars_str = "⭐" * stars
        text += f"{stars_str} от @{username or 'аноним'}\n"
        if comment:
            text += f"   {comment}\n"
        text += f"   <i>{created_at}</i>\n\n"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=mentor_actions_menu(mentor_id)
    )
    await callback.answer()


# ===== МОЙ ПРОФИЛЬ МЕНТОРА =====

@router.callback_query(F.data == "mentor:profile")
async def callback_mentor_profile(callback: CallbackQuery):
    mentor = get_mentor(callback.from_user.id)

    if not mentor:
        await callback.answer("⚠️ Ты не ментор. Стань ментором через /mentor", show_alert=True)
        return

    uid, games, roles, time, description, is_active, rating, sessions, created_at = mentor

    await callback.message.edit_text(
        f"🎓 <b>Твой профиль ментора</b>\n\n"
        f"🎮 Игры: {games}\n"
        f"🎯 Роли: {roles or '—'}\n"
        f"🕐 Время: {time or '—'}\n"
        f"📝 Описание: {description or '—'}\n\n"
        f"⭐ Рейтинг: {rating}/10\n"
        f"📊 Сессий: {sessions}\n\n"
        f"Чтобы обновить профиль — стань ментором заново.",
        parse_mode="HTML",
        reply_markup=mentor_menu()
    )
    await callback.answer()


# ===== ПЕРЕСТАТЬ БЫТЬ МЕНТОРОМ =====

@router.callback_query(F.data == "mentor:leave")
async def callback_mentor_leave(callback: CallbackQuery):
    if not is_mentor(callback.from_user.id):
        await callback.answer("⚠️ Ты не ментор", show_alert=True)
        return

    success = remove_mentor(callback.from_user.id)

    if success:
        await callback.message.edit_text(
            "✅ <b>Ты больше не ментор</b>\n\n"
            "Если захочешь вернуться — /mentor → «Стать ментором».",
            parse_mode="HTML",
            reply_markup=mentor_menu()
        )
    else:
        await callback.answer("❌ Ошибка", show_alert=True)

    await callback.answer()