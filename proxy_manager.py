import asyncio
import time
import urllib.request
import aiohttp
from aiohttp_socks import ProxyConnector

# ===== НАСТРОЙКИ =====
PROXY_FILE = "proxies.txt"
WORKING_FILE = "working_proxies.txt"
TEST_URL = "https://api.telegram.org"
TIMEOUT = 8  # секунд на проверку одного прокси
MAX_PROXIES = 300  # сколько прокси скачивать (не тысячи)

# GitHub-источники (пробуем по очереди)
PROXY_SOURCES = [
    # Proxifly — обновляется каждые 5 минут, ~20 000 прокси
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    # ProxyScrape — обновляется каждые 5 минут
    "https://raw.githubusercontent.com/ProxyScrape/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    # TheSpeedX — старая, но стабильная
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    # ShiftyTR — альтернатива
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
]


def download_proxies_from_github() -> bool:
    """
    Скачивает свежий список SOCKS5-прокси с GitHub.
    Пробует источники по очереди, пока один не сработает.
    Возвращает True, если удалось.
    """
    for url in PROXY_SOURCES:
        source = url.split("/")[3]  # имя репозитория
        try:
            print(f"🌐 Пробую {source}...")
            with urllib.request.urlopen(url, timeout=15) as resp:
                content = resp.read().decode("utf-8")
                lines = [l.strip() for l in content.splitlines() if l.strip()]

            if not lines:
                print(f"⚠️ {source} вернул пустой список")
                continue

            # Нормализуем формат: добавляем socks5:// где нужно
            normalized = []
            for p in lines:
                if not p.startswith(("socks", "http")):
                    p = f"socks5://{p}"
                normalized.append(p)

            # Берём первые MAX_PROXIES
            selected = normalized[:MAX_PROXIES]

            with open(PROXY_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(selected))

            print(f"✅ Загружено {len(selected)} прокси с {source}")
            return True

        except Exception as e:
            print(f"⚠️ {source} не сработал: {type(e).__name__}")
            continue

    print("❌ Не удалось скачать прокси ни с одного источника")
    return False


def load_proxies() -> list[str]:
    """Читает прокси из файла."""
    try:
        with open(PROXY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []

    return [
        line.strip() for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]


async def check_proxy(proxy_url: str) -> dict:
    """Проверяет один прокси. Возвращает dict с результатом."""
    result = {
        "proxy": proxy_url,
        "works": False,
        "status": None,
        "error": None,
        "time": None,
    }

    try:
        start = time.time()

        # SOCKS5/SOCKS4 через ProxyConnector
        if proxy_url.startswith("socks"):
            connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(TEST_URL, timeout=TIMEOUT) as resp:
                    result["works"] = True
                    result["status"] = resp.status
                    result["time"] = round(time.time() - start, 2)
        # HTTP через обычный proxy-параметр
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    TEST_URL, proxy=proxy_url, timeout=TIMEOUT
                ) as resp:
                    result["works"] = True
                    result["status"] = resp.status
                    result["time"] = round(time.time() - start, 2)

    except asyncio.TimeoutError:
        result["error"] = "Таймаут"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:80]}"

    return result


async def find_best_proxies(limit: int = 5) -> list[str]:
    """
    Проверяет все прокси параллельно, возвращает список рабочих,
    отсортированных по скорости (быстрые — первыми).
    Сохраняет рабочие в working_proxies.txt.
    """
    proxies = load_proxies()

    if not proxies:
        print("❌ Нет прокси для проверки.")
        return []

    print(f"🔍 Проверяю {len(proxies)} прокси...")

    # Проверяем все параллельно
    tasks = [check_proxy(p) for p in proxies]
    results = await asyncio.gather(*tasks)

    # Фильтруем рабочие
    working = [r for r in results if r["works"]]
    working.sort(key=lambda r: r["time"])

    print(f"✅ Рабочих: {len(working)} из {len(proxies)}")
    for r in working[:limit]:
        print(f"   ⚡ {r['proxy']} — {r['time']} сек")

    # Сохраняем рабочие в файл
    if working:
        with open(WORKING_FILE, "w", encoding="utf-8") as f:
            for r in working:
                f.write(r["proxy"] + "\n")
        print(f"💾 Сохранено в {WORKING_FILE}")

    return [r["proxy"] for r in working]


async def get_working_proxy() -> str | None:
    """Возвращает лучший рабочий прокси или None."""
    best = await find_best_proxies(limit=5)
    return best[0] if best else None

async def get_all_working_proxies(limit: int = 20) -> list[str]:
    """
    Возвращает все рабочие прокси, отсортированные по скорости.
    Используется для ротации.
    """
    proxies = load_proxies()

    if not proxies:
        print("❌ Нет прокси для проверки.")
        return []

    print(f"🔍 Проверяю {len(proxies)} прокси...")

    tasks = [check_proxy(p) for p in proxies]
    results = await asyncio.gather(*tasks)

    working = [r for r in results if r["works"]]
    working.sort(key=lambda r: r["time"])

    print(f"✅ Рабочих: {len(working)} из {len(proxies)}")
    for r in working[:limit]:
        print(f"   ⚡ {r['proxy']} — {r['time']} сек")

    if working:
        with open(WORKING_FILE, "w", encoding="utf-8") as f:
            for r in working:
                f.write(r["proxy"] + "\n")
        print(f"💾 Сохранено в {WORKING_FILE}")

    return [r["proxy"] for r in working]


async def check_single_proxy(proxy_url: str) -> bool:
    """Быстрая проверка одного прокси. True — рабочий."""
    result = await check_proxy(proxy_url)
    return result["works"]