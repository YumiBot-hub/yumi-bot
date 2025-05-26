import os
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

if __name__ == "__main__":
    import asyncio

    # Set Webhook automatisch beim Start (optional)
    import requests
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # z.B. https://deinbot.onrender.com/webhook

    if TELEGRAM_TOKEN and WEBHOOK_URL:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            data={"url": WEBHOOK_URL}
        )
        print(f"📡 Webhook gesetzt: {r.json()}")

    port = int(os.getenv("PORT", 10000))

    async def main():
        await start_bot()

    # Starte Telegram Bot im Hintergrund
    asyncio.create_task(main())

    # Starte FastAPI Webserver
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
