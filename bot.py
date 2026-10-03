import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError

from database import (
    init_db, init_analytics, migrate_db, init_games, init_messages
)
from proxy_manager import download_proxies_from_github, find_best_proxies

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)


async def try_start_bot(proxy_url: str | None) -> bool:
    if proxy_url:
        print(f"🚀 Запуск с прокси: {proxy_url}")
        session = AiohttpSession(proxy=proxy_url)
    else:
        print("🚀 Запуск без прокси (напрямую)")
        session = AiohttpSession()

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    import importlib
    import handlers
    import admin
    importlib.reload(handlers)
    importlib.reload(admin)

    dp.include_router(handlers.router)
    dp.include_router(admin.router)

    try:
        await dp.start_polling(bot)
        return True
    except TelegramNetworkError as e:
        print(f"❌ Сетевая ошибка: {str(e)[:150]}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:150]}")
        return False
    finally:
        await bot.session.close()


async def main():
    init_db()
    migrate_db()
    init_analytics()
    init_games()
    init_messages()

    print()
    print("=" * 60)
    print("Попытка 1: прямое подключение")
    print("=" * 60)

    if await try_start_bot(None):
        return

    print()
    print("=" * 60)
    print("Попытка 2: через прокси с GitHub")
    print("=" * 60)

    if not download_proxies_from_github():
        print()
        print("❌ Не удалось скачать прокси с GitHub.")
        return

    proxies = await find_best_proxies(limit=10)

    if not proxies:
        print()
        print("❌ Рабочих прокси не найдено.")
        return

    for i, proxy in enumerate(proxies, 1):
        print()
        print("=" * 60)
        print(f"Попытка {i + 2}: {proxy}")
        print("=" * 60)

        if await try_start_bot(proxy):
            return

    print()
    print("❌ Все прокси перебраны.")


if __name__ == "__main__":
    asyncio.run(main())