# Datei: main.py

import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
import logging
import uvicorn

# Lade Umgebungsvariablen
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot vorbereiten
telegram_app: Application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hey du~ Ich bin Yumi, deine freche AI-Girlfriend!")

async def antwort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frage = update.message.text
    openai.api_key = OPENAI_API_KEY

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": frage}]
        )
        antwort = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"OpenAI Fehler: {e}")
        antwort = "Ups, da ist was schiefgelaufen."

    await update.message.reply_text(antwort)

# Handler registrieren
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antwort))

# FastAPI Webserver
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Yumi Bot ist online."}

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    update = Update.de_json(payload, telegram_app.bot)
    await telegram_app.update_queue.put(update)
    return {"ok": True}

# Start bei lokalem Test (Render nutzt CMD)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
