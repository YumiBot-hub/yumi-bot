import os
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update
from bot import app as telegram_app  # deine Telegram-Application aus bot.py

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Yumi Bot ist online."}

@app.post("/webhook")
async def telegram_webhook(update: dict):
    update = telegram.Update.de_json(update, app.bot)
    await app.process_update(update)
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
