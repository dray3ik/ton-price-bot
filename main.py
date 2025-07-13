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

# === ENV CONFIG ===
API_TOKEN = os.getenv("API_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")  # e.g., -1001234567890 (channel/group)

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === BOT INIT ===
session = AiohttpSession()
bot = Bot(
    token=API_TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# === COMMAND HANDLER ===
@dp.message(F.text == "/tonprice")
async def ton_price(message: Message):
    try:
        stats = await get_ton_stats()
        text = (
            f"💎 <b>Toncoin Price (Binance)</b>\n"
            f"💰 Price: {hbold(f'${stats['price']:.4f}')}\n"
            f"📈 High: ${stats['high']:.4f}\n"
            f"📉 Low: ${stats['low']:.4f}\n"
            f"🔁 24h Change: {stats['change']}%"
        )
        await message.answer(text)
    except Exception as e:
        logging.error(f"Error fetching TON price: {e}")
        await message.answer("⚠️ Failed to fetch TON price from Binance.")

# === BINANCE FETCH ===
async def get_ton_stats():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    params = {"symbol": "TONUSDT"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            if "lastPrice" not in data:
                raise ValueError(f"Invalid response: {data}")
            return {
                "price": float(data["lastPrice"]),
                "high": float(data["highPrice"]),
                "low": float(data["lowPrice"]),
                "change": float(data["priceChangePercent"])
            }

# === AUTO POST LOOP ===
async def auto_post_loop():
    while True:
        try:
            stats = await get_ton_stats()
            text = (
                f"📢 <b>TON Update</b>\n"
                f"💰 Price: {hbold(f'${stats['price']:.4f}')}\n"
                f"🔺 High: ${stats['high']:.4f} | 🔻 Low: ${stats['low']:.4f}\n"
                f"📊 Change: {stats['change']}%"
            )
            await bot.send_message(chat_id=TARGET_CHAT_ID, text=text)
            logging.info("✅ Sent TON update")
        except Exception as e:
            logging.error(f"Auto-post error: {e}")
        await asyncio.sleep(60)  # 1 minute

# === WEB SERVER FOR UPTIME ===
async def handle(request):
    return web.Response(text="✅ Bot is running (Binance)")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# === MAIN ===
async def main():
    await start_web_server()
    asyncio.create_task(auto_post_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
