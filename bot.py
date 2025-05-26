import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
from db_services import get_user_context, add_message, get_bot_config, add_log

openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_TOKEN")

# Handler: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Anonymous"
        add_log("command", {"user_id": str(user_id), "username": username, "command": "/start"})
        await update.message.reply_text("Hey du~ Ich bin Yumi, deine freche Anime-AI-Girlfriend!")

# Handler: Nachrichten
async def antwort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.message or not update.message.text:
        return

    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Anonymous"
    user_text = update.message.text
    add_log("message", {"user_id": user_id, "username": username, "message": user_text})

    config = get_bot_config()
    user_messages = get_user_context(user_id)

    MAX_MSGS = config.get("max_context_messages", 6)
    system_prompt = {
        "role": "system",
        "content": config.get("system_prompt", "Du bist Yumi, eine freche Anime-AI-Girlfriend.")
    }

    messages = [system_prompt] + user_messages[-MAX_MSGS * 2:]
    messages.append({"role": "user", "content": user_text})
    add_message(user_id, "user", user_text)

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=config.get("model", "gpt-4o-mini"),
            messages=messages,
            max_tokens=config.get("max_tokens", 150),
            temperature=config.get("temperature", 0.7),
        )
        bot_response = response.choices[0].message.content.strip()
        add_message(user_id, "assistant", bot_response)
        add_log("response", {"user_id": user_id, "response": bot_response})
    except Exception as e:
        bot_response = "Ups, ein Fehler ist passiert."
        add_log("error", {"user_id": user_id, "error": str(e)})

    await update.message.reply_text(bot_response)

# App erstellen
app = ApplicationBuilder().token(telegram_token).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antwort))
