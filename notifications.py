import asyncio
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError

from database import (
    get_pending_notifications,
    mark_notification_sent,
    cleanup_old_notifications,
    get_profile,
    is_profile_filled,
)


async def send_mutual_match_notification(bot: Bot, user_id: int, data: str):
    """
    Уведомление о взаимном мэтче.
    data = "other_id|other_name"
    """
    try:
        other_id, other_name = data.split("|", 1)
    except ValueError:
        return

    text = (
        f"🤝 <b>Взаимный мэтч!</b>\n\n"
        f"@{other_name} тоже тебя выбрал(а).\n\n"
        f"Самое время сыграть вместе!\n"
        f"Написать: /msg_{other_id}\n"
        f"Диалог: /chat {other_id}"
    )

    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
    except TelegramNetworkError as e:
        print(f"⚠️ Не удалось отправить уведомление {user_id}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка уведомления: {e}")


async def send_rate_reminder(bot: Bot, user_id: int, data: str):
    """
    Напоминание оценить напарника.
    data = "other_id|other_name"
    """
    try:
        other_id, other_name = data.split("|", 1)
    except ValueError:
        return

    text = (
        f"⭐ <b>Не забудь оценить напарника</b>\n\n"
        f"Ты играл(а) с @{other_name}.\n\n"
        f"Оцени его/её: /rate {other_id}\n\n"
        f"<i>Оценка помогает другим найти хороших напарников.</i>"
    )

    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
    except TelegramNetworkError as e:
        print(f"⚠️ Не удалось отправить уведомление {user_id}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка уведомления: {e}")


async def send_profile_reminder(bot: Bot, user_id: int, data: str = ""):
    """
    Напоминание заполнить профиль.
    """
    user = get_profile(user_id)
    if not user:
        return

    # Если профиль уже заполнен — не напоминаем
    if is_profile_filled(user_id):
        return

    text = (
        f"📝 <b>Заполни профиль</b>\n\n"
        f"Ты ещё не заполнил(а) профиль.\n\n"
        f"Без профиля ты не сможешь искать напарников.\n\n"
        f"Заполнить: /profile"
    )

    try:
        await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
    except TelegramNetworkError as e:
        print(f"⚠️ Не удалось отправить уведомление {user_id}: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка уведомления: {e}")


async def process_notifications(bot: Bot):
    """
    Обрабатывает все ожидающие уведомления.
    Вызывается из фонового цикла.
    """
    notifications = get_pending_notifications(limit=50)

    if not notifications:
        return

    print(f"📬 Обрабатываю {len(notifications)} уведомлений...")

    for notif_id, user_id, notif_type, data in notifications:
        try:
            if notif_type == "mutual_match":
                await send_mutual_match_notification(bot, user_id, data)
            elif notif_type == "rate_reminder":
                await send_rate_reminder(bot, user_id, data)
            elif notif_type == "profile_reminder":
                await send_profile_reminder(bot, user_id, data)
            else:
                print(f"⚠️ Неизвестный тип уведомления: {notif_type}")

            mark_notification_sent(notif_id)
        except Exception as e:
            print(f"⚠️ Ошибка обработки уведомления #{notif_id}: {e}")
            # Помечаем как отправленное, чтобы не зациклиться
            mark_notification_sent(notif_id)

        # Пауза между уведомлениями, чтобы не превысить лимиты Telegram
        await asyncio.sleep(0.1)


async def notification_worker(bot: Bot, interval: int = 30):
    """
    Фоновый воркер: каждые interval секунд проверяет уведомления.
    """
    print(f"🔔 Воркер уведомлений запущен (интервал: {interval} сек)")

    while True:
        try:
            await process_notifications(bot)
        except Exception as e:
            print(f"⚠️ Ошибка воркера уведомлений: {e}")

        await asyncio.sleep(interval)


async def cleanup_worker(interval_hours: int = 24):
    """
    Фоновый воркер: раз в сутки чистит старые уведомления.
    """
    while True:
        try:
            cleanup_old_notifications(days=7)
            print("🧹 Старые уведомления очищены")
        except Exception as e:
            print(f"⚠️ Ошибка очистки: {e}")

        await asyncio.sleep(interval_hours * 3600)