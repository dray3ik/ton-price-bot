import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import web
import aiohttp
import os

# === CONFIG ===
API_TOKEN = os.getenv("API_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")  # e.g., -1001234567890 for channel/group

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === BOT INIT ===
session = AiohttpSession()
bot = Bot(token=API_TOKEN, session=session, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# === HANDLERS ===
@dp.message(F.text == "/tonprice")
async def ton_price(message: Message):
    try:
        price = await get_ton_price()
        await message.answer(f"💰 Toncoin price: {hbold(f'${price:.4f}')}")
    except Exception as e:
        logging.error(f"Error fetching TON price: {e}")
        await message.answer("⚠️ Failed to fetch TON price. Try again later.")

# === FETCH TON PRICE FROM COINGECKO ===
async def get_ton_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "toncoin", "vs_currencies": "usd"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            if "toncoin" not in data:
                raise ValueError(f"Invalid response: {data}")
            return data["toncoin"]["usd"]

# === AUTO POST TO CHANNEL ===
async def auto_post_loop():
    while True:
        try:
            price = await get_ton_price()
            text = f"📈 1 TON = {hbold(f'${price:.4f}')}"
            await bot.send_message(chat_id=TARGET_CHAT_ID, text=text)
            logging.info("✅ Sent auto update")
        except Exception as e:
            logging.error(f"Auto-post error: {e}")
        await asyncio.sleep(60)  # 1 minute

# === WEB SERVER FOR UPTIMEROBOT ===
async def handle(request):
    return web.Response(text="✅ Bot is running")

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
