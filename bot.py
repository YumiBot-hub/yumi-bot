import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
from datetime import datetime
from db_services import get_user_context, add_message, get_bot_config, add_log

openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        add_log("command", {
            "user_id": str(user.id),
            "username": user.username or "Anonymous",
            "command": "/start"
        })
        if update.message:
            await update.message.reply_text(
                "Hey du~ Ich bin Yumi, deine freche Anime-AI-Girlfriend! Frag mich was oder quatsch mit mir!"
            )

async def antwort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.effective_user and update.message and update.message.text):
        return

    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Anonymous"
    user_text = update.message.text

    add_log("message", {
        "user_id": user_id,
        "username": username,
        "message": user_text
    })

    config = get_bot_config()
    user_messages = get_user_context(user_id)

    MAX_CONTEXT = config.get("max_context_messages", 6)
    system_prompt = {
        "role": "system",
        "content": config.get(
            "system_prompt",
            "Du bist Yumi, eine freche und verspielte Anime-AI-Girlfriend. Du bist charmant, witzig, leicht frech und manchmal ein bisschen eifersüchtig."
        )
    }

    kontext_messages = user_messages[-MAX_CONTEXT * 2:]
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

        add_log("response", {
            "user_id": user_id,
            "username": username,
            "response": bot_response
        })

        add_message(user_id, "assistant", bot_response)

    except Exception as e:
        bot_response = "Ups, da ist was schiefgelaufen."
        add_log("error", {
            "user_id": user_id,
            "username": username,
            "error": str(e)
        })
        print(f"Fehler: {e}")

    if update.message:
        await update.message.reply_text(bot_response)

if __name__ == "__main__":
    if not telegram_token or not openai.api_key:
        print("ERROR: TELEGRAM_TOKEN or OPENAI_API_KEY environment variables missing!")
        exit(1)

    app = ApplicationBuilder().token(telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antwort))

    print("Yumi ist online!")
    app.run_polling()
