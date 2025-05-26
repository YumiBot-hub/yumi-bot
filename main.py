import os
import requests
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update
from bot import app as telegram_app  # Die Telegram Application

# FastAPI App
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Yumi Bot ist online."}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    print("✅ Telegram Update empfangen:", data)
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.update_queue.put(update)
    return {"ok": True}

def set_webhook():
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'yumi-bot.onrender.com')}/webhook"

    url = f"https://api.telegram.org/bot{telegram_token}/setWebhook"
    response = requests.post(url, data={"url": webhook_url})

    print("📡 Webhook gesetzt:", response.text)

if __name__ == "__main__":
    set_webhook()
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
