import os
import openai
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from db_services import get_user_context, add_message, get_bot_config, update_bot_config, add_log

# Telegram & OpenAI Setup
openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_TOKEN")
webhook_url = os.getenv("WEBHOOK_URL")  # z. B. https://dein-bot.onrender.com

# FastAPI App
app = FastAPI()

# Telegram Bot Application
telegram_app = Application.builder().token(telegram_token).build()

# === HANDLER ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Anonymous"
        add_log("command", {"user_id": str(user_id), "username": username, "command": "/start"})
        if update.message:
            await update.message.reply_text("Hey du~ Ich bin Yumi, deine freche Anime-AI-Girlfriend! Frag mich was oder quatsch mit mir!")

async def antwort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message or not update.message.text:
        return

    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Anonymous"
    user_text = update.message.text
    add_log("message", {"user_id": user_id, "username": username, "message": user_text})

    config = get_bot_config()
    user_messages = get_user_context(user_id)

    MAX_KONTAKT_NACHRICHTEN = config.get("max_context_messages", 6)
    system_prompt = {
        "role": "system",
        "content": config.get("system_prompt", "Du bist Yumi, eine freche und verspielte Anime-AI-Girlfriend. Du bist charmant, witzig, leicht frech und manchmal ein bisschen eifersüchtig.")
    }

    kontext_messages = user_messages[-MAX_KONTAKT_NACHRICHTEN*2:]
    add_message(user_id, "user", user_text)
    kontext_messages.append({"role": "user", "content": user_text})
    messages = [system_prompt] + kontext_messages

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model=config.get("model", "gpt-4o-mini"),
            messages=messages,
            max_tokens=config.get("max_tokens", 150),
            temperature=config.get("temperature", 0.7),
        )
        bot_response = response.choices[0].message.content.strip()
        add_log("response", {"user_id": user_id, "username": username, "response": bot_response})
        add_message(user_id, "assistant", bot_response)
    except Exception as e:
        bot_response = "Ups, da ist was schiefgelaufen."
        add_log("error", {"user_id": user_id, "username": username, "error": str(e)})
        print(f"Fehler: {e}")

    if update.message:
        await update.message.reply_text(bot_response)

# === REGISTRIERE HANDLER ===
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antwort))

# === FASTAPI: Webhook Endpoint ===
@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# === BEIM START: Setze den Telegram Webhook ===
@app.on_event("startup")
async def startup():
    await telegram_app.bot.set_webhook(f"{webhook_url}/webhook")
    add_log("bot_start", {"message": "Webhook gesetzt"})
    print("Webhook wurde gesetzt und Yumi ist bereit!")
