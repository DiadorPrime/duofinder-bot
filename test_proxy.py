import asyncio
from aiohttp_socks import ProxyConnector
import aiohttp


async def test_proxy():
    proxy_url = "socks5://69.61.200.104:36181"  # замени на свой

    try:
        connector = ProxyConnector.from_url(proxy_url)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get("https://api.telegram.org", timeout=10) as resp:
                print(f"✅ Прокси работает! Статус: {resp.status}")
    except Exception as e:
        print(f"❌ Прокси не работает: {e}")


asyncio.run(test_proxy())