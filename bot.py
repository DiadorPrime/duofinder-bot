import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database import (
    init_db, init_analytics, migrate_db, init_games, init_messages,
    init_ratings_extended, init_reports, init_game_data
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)


async def main():
    """Запуск бота на Amvera (без прокси — Amvera проксирует сама)."""
    init_db()
    migrate_db()
    init_analytics()
    init_games()
    init_messages()
    init_ratings_extended()
    init_reports()
    init_game_data()

    print("🚀 Запуск бота на Amvera...")
    print(f"📁 База данных: {os.path.abspath('duofinder.db')}")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Перезагружаем модули, чтобы router'ы создались заново
    import importlib
    import handlers
    import admin
    importlib.reload(handlers)
    importlib.reload(admin)

    dp.include_router(handlers.router)
    dp.include_router(admin.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("👋 Бот остановлен (Ctrl + C)")
        print("=" * 60)