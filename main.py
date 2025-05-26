import os
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update
from bot import app as telegram_app  # Das ist die Telegram-App

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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
