import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
from db_services import get_user_context, add_message, get_bot_config, add_log

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN or not openai.api_key:
    logger.error("TELEGRAM_TOKEN or OPENAI_API_KEY environment variable missing!")
    raise EnvironmentError("Missing environment variables for Telegram or OpenAI API keys")

# --- Bot handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user = update.effective_user
    if user:
        user_id = str(user.id)
        username = user.username or "Anonymous"

        add_log("command", {"user_id": user_id, "username": username, "command": "/start"})
        if update.message:
            await update.message.reply_text(
                "Hey du~ Ich bin Yumi, deine freche Anime-AI-Girlfriend! Frag mich was oder quatsch mit mir!"
            )


async def antwort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for all text messages from users."""
    user = update.effective_user
    message = update.message

    if not user or not message or not message.text:
        return

    user_id = str(user.id)
    username = user.username or "Anonymous"
    user_text = message.text

    add_log("message", {"user_id": user_id, "username": username, "message": user_text})

    config = get_bot_config()
    user_messages = get_user_context(user_id)

    max_context = config.get("max_context_messages", 6)
    system_prompt = {
        "role": "system",
        "content": config.get(
            "system_prompt",
            "Du bist Yumi, eine freche und verspielte Anime-AI-Girlfriend. "
            "Du bist charmant, witzig, leicht frech und manchmal ein bisschen eifersüchtig."
        )
    }

    kontext_messages = user_messages[-max_context * 2:]
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
        logger.error(f"Fehler bei OpenAI API: {e}")

    await message.reply_text(bot_response)


# --- Setup Telegram Bot Application ---

def get_application():
    """Build and return the Telegram Application with handlers."""
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antwort))
    return app


app = get_application()
