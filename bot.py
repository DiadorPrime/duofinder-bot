import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError

from database import (
    init_db, init_analytics, migrate_db, init_games, init_messages,
    init_ratings_extended
)
from proxy_manager import (
    download_proxies_from_github,
    get_all_working_proxies,
    check_single_proxy,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)


# ===== ЗАПУСК БОТА С ПРОКСИ =====

async def run_bot_with_proxy(proxy_url: str | None):
    """
    Запускает бота с указанным прокси.
    Возвращает True, если бот упал по сети (нужна смена прокси).
    Возвращает False, если бот упал по другой причине.
    """
    if proxy_url:
        print(f"🚀 Запуск с прокси: {proxy_url}")
        session = AiohttpSession(proxy=proxy_url)
    else:
        print("🚀 Запуск без прокси (напрямую)")
        session = AiohttpSession()

    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())

    # Перезагружаем модули, чтобы router'ы создались заново
    import importlib
    import handlers
    import admin
    importlib.reload(handlers)
    importlib.reload(admin)

    dp.include_router(handlers.router)
    dp.include_router(admin.router)

    try:
        await dp.start_polling(bot)
        # Если polling завершился без ошибки — выходим
        return False
    except TelegramNetworkError as e:
        print(f"❌ Сетевая ошибка: {str(e)[:150]}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:150]}")
        return False
    finally:
        try:
            await bot.session.close()
        except Exception:
            pass


# ===== ГЛАВНЫЙ ЦИКЛ С АВТОСМЕНОЙ =====

async def main():
    init_db()
    migrate_db()
    init_analytics()
    init_games()
    init_messages()
    init_ratings_extended()  # ← добавляем

    print()
    print("=" * 60)
    print("🎮 DuoFinder Bot — запуск с автосменой прокси")
    print("=" * 60)

    cycle = 0

    while True:
        cycle += 1

        print()
        print("=" * 60)
        print(f"ЦИКЛ #{cycle}")
        print("=" * 60)

        # Попытка 1: прямое подключение (вдруг VPN)
        print()
        print("Попытка: прямое подключение")
        print("-" * 60)
        network_error = await run_bot_with_proxy(None)

        if not network_error:
            # Если упал не по сети — что-то другое, выходим
            print("⚠️ Бот остановился (не сетевая ошибка). Выход.")
            return

        # Попытка 2: скачиваем свежие прокси
        print()
        print("Скачиваю свежие прокси с GitHub...")
        print("-" * 60)
        if not download_proxies_from_github():
            print("❌ Не удалось скачать прокси. Ждём 60 сек...")
            await asyncio.sleep(60)
            continue

        # Проверяем все прокси
        proxies = await get_all_working_proxies(limit=20)

        if not proxies:
            print("❌ Рабочих прокси не найдено. Ждём 60 сек...")
            await asyncio.sleep(60)
            continue

        print()
        print(f"✅ Найдено {len(proxies)} рабочих прокси. Пробую по очереди...")
        print("-" * 60)

        # Пробуем прокси по очереди
        switched = False

        for i, proxy in enumerate(proxies, 1):
            print()
            print(f"Прокси {i}/{len(proxies)}")
            print("-" * 60)

            # Быстрая проверка перед запуском
            print(f"⏱  Проверяю прокси...")
            if not await check_single_proxy(proxy):
                print(f"❌ Прокси не работает, пропускаю")
                continue

            print(f"✅ Прокси рабочий, запускаю бота...")
            network_error = await run_bot_with_proxy(proxy)

            if not network_error:
                # Упал не по сети — выходим
                print("⚠️ Бот остановился (не сетевая ошибка). Выход.")
                return

            # Прокси умер во время работы — пробуем следующий
            print(f"⚠️ Прокси умер во время работы. Переключаюсь на следующий...")
            switched = True

            # Небольшая пауза перед следующим
            await asyncio.sleep(2)

        # Все прокси перебраны
        if switched:
            print()
            print("🔄 Все прокси перебраны. Скачиваю свежие...")
            await asyncio.sleep(10)
        else:
            print()
            print("❌ Ни один прокси не сработал. Ждём 60 сек...")
            await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("👋 Бот остановлен пользователем (Ctrl + C)")
        print("=" * 60)