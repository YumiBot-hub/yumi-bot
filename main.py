import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from bot import get_application
import asyncio
import httpx

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ENV
PORT = int(os.environ.get("PORT", 10000))
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# FastAPI App
app = FastAPI()
telegram_app = get_application()

# FastAPI: root test
@app.get("/")
def home():
    return {"status": "ok"}

# FastAPI: Webhook Endpoint
@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    logger.info("✅ Telegram Update empfangen: %s", data)
    return {"ok": True}

# FastAPI: Startup -> Telegram Bot Initialisieren + Webhook setzen
@app.on_event("startup")
async def on_startup():
    await telegram_app.initialize()  # <- Wichtig
    await telegram_app.start()
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            params={"url": WEBHOOK_URL}
        )
        logger.info("📡 Webhook gesetzt: %s", r.json())

# FastAPI: Shutdown
@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()
