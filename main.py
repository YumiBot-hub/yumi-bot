import os
import asyncio
import requests
import uvicorn
from fastapi import FastAPI, Request
from telegram import Update
from bot import app as telegram_app, start_bot

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Yumi Bot ist online."}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.update_queue.put(update)
    return {"ok": True}

async def set_webhook():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    if TELEGRAM_TOKEN and WEBHOOK_URL:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            data={"url": WEBHOOK_URL}
        )
        print(f"📡 Webhook gesetzt: {r.json()}")

async def main():
    await set_webhook()
    # Telegram-Bot starten
    asyncio.create_task(start_bot())
    # Uvicorn dauerhaft starten
    config = uvicorn.Config("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
