import asyncio
import logging
import os
from aiohttp import web
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.markdown import hbold

API_TOKEN = os.getenv("API_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")

logging.basicConfig(level=logging.INFO)

session = AiohttpSession()
bot = Bot(
    token=API_TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


@dp.message(F.text == "/tonprice")
async def ton_price(message: Message):
    try:
        stats = await get_ton_stats()
        text = (
            f"💎 <b>Toncoin Price</b>\n"
            f"💰 Price: {hbold(f'${stats['price']:.4f}')}\n"
            f"📈 High: ${stats['high']:.4f} | 📉 Low: ${stats['low']:.4f}\n"
            f"🔄 Change: {stats['change']}%"
        )
        await message.answer(text)
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("⚠️ Failed to fetch TON price.")


async def get_ton_stats():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    params = {"symbol": "TONUSDT"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if "lastPrice" not in data:
                raise ValueError(f"Invalid response: {data}")
            return {
                "price": float(data["lastPrice"]),
                "high": float(data["highPrice"]),
                "low": float(data["lowPrice"]),
                "change": float(data["priceChangePercent"]),
            }


async def auto_post_loop():
    while True:
        try:
            stats = await get_ton_stats()
            text = (
                f"📢 <b>TON Auto Update</b>\n"
                f"💰 Price: {hbold(f'${stats['price']:.4f}')}\n"
                f"📈 High: ${stats['high']:.4f} | 📉 Low: ${stats['low']:.4f}\n"
                f"🔄 Change: {stats['change']}%"
            )
            await bot.send_message(chat_id=TARGET_CHAT_ID, text=text)
            logging.info("✅ Sent update")
        except Exception as e:
            logging.error(f"Post error: {e}")
        await asyncio.sleep(60)


async def handle(request):
    return web.Response(text="✅ Bot is running.")


async def start_web():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()


async def main():
    await start_web()
    asyncio.create_task(auto_post_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
