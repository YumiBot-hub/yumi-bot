import os
import logging
import requests
import asyncio
import uvicorn
from fastapi import FastAPI, Request
from telegram import Update
from bot import get_application  # aus deiner bot.py

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI()

# Telegram Bot Application
telegram_app = get_application()

WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"

@app.get("/")
async def root():
    return {"message": "Yumi Bot ist online."}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    logger.info(f"✅ Telegram Update empfangen: {data}")
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.update_queue.put(update)
    return {"ok": True}

async def main():
    # Starte Telegram Application
    asyncio.create_task(telegram_app.initialize())
    asyncio.create_task(telegram_app.start())

    # Webhook setzen
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{os.getenv('TELEGRAM_TOKEN')}/setWebhook",
            data={"url": WEBHOOK_URL},
            timeout=10
        )
        logger.info(f"📡 Webhook gesetzt: {response.json()}")
    except Exception as e:
        logger.error(f"Fehler beim Setzen des Webhooks: {e}")

    # Starte FastAPI Server
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
