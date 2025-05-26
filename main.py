import os
import logging
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import httpx

from bot import app as telegram_app  # Telegram Application
from telegram import Update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # z. B. https://dein-bot-name.onrender.com/webhook

if not BOT_TOKEN or not WEBHOOK_URL:
    raise EnvironmentError("TELEGRAM_TOKEN oder WEBHOOK_URL fehlen!")

# Lifespan ersetzt @app.on_event("startup") und @app.on_event("shutdown")
@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.start()

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            params={"url": f"{WEBHOOK_URL}/webhook"}
        )
        logger.info("📡 Webhook gesetzt: %s", r.json())

    yield  # App läuft hier

    await telegram_app.stop()
    await telegram_app.shutdown()

# FastAPI-App mit Lifespan
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Yumi Telegram Bot ist online!"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    logger.info("✅ Telegram Update empfangen: %s", data)
    await telegram_app.process_update(update)
    return {"status": "ok"}
