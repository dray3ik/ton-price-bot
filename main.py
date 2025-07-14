import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiohttp import ClientSession, web

# ========== CONFIG ==========
BOT_TOKEN = "YOUR_ACTUAL_BOT_TOKEN"        # <-- Replace with your bot token
CHANNEL_ID = "@yourchannel"                # <-- Replace with @channelname or -1001234567890
BINANCE_API = "https://api.binance.com/api/v3/ticker/price?symbol=TONUSDT"
# ============================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# === Fetch Toncoin price from Binance ===
async def get_ton_price():
    async with ClientSession() as session:
        async with session.get(BINANCE_API) as resp:
            data = await resp.json()
            return float(data["price"])

# === Task: post price every 60 seconds ===
async def post_price_task():
    await bot.delete_webhook(drop_pending_updates=True)
    while True:
        try:
            price = await get_ton_price()
            text = f"💎 <b>Toncoin Price (Binance):</b> ${price:.4f}"
            await bot.send_message(CHANNEL_ID, text)
        except Exception as e:
            logging.error(f"[POST ERROR] {e}")
        await asyncio.sleep(60)

# === Simple HTTP route for UptimeRobot ===
async def handle_ping(request):
    return web.Response(text="Bot is alive!")

# === Start a web server for Render/UptimeRobot ===
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# === Startup event for Aiogram Dispatcher ===
@dp.startup()
async def on_startup(dispatcher: Dispatcher):
    asyncio.create_task(post_price_task())

# === Main function ===
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
