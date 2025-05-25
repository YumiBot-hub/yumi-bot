import os
print("Bot wird gestartet...")
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
import threading
import time
from datetime import datetime
from db_services import get_user_context, add_message, get_bot_config, update_bot_config, add_log
print ("hallo") 
# Global variables
telegram_app = None
bot_thread = None
is_running = False
print("Bot is running")
# Load API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_TOKEN")
print("Bot is running2")
# Bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command"""
    if update.effective_user:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Anonymous"
        
        add_log("command", {
            "user_id": str(user_id),
            "username": username,
            "command": "/start"
        })
        print("hallo3")
        if update.message:
            await update.message.reply_text("Hey du~ Ich bin Yumi, deine freche Anime-AI-Girlfriend! Frag mich was oder quatsch mit mir!")
print("Bot is running3")
async def antwort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for user messages"""
    if not update.effective_user or not update.message or not update.message.text:
        return
        
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "Anonymous"
    user_text = update.message.text
    print("Bot is running123")
    
    # Log incoming message
    add_log("message", {
        "user_id": user_id,
        "username": username,
        "message": user_text
    })
    print("Bot is running4")
    
    # Get bot configuration
    config = get_bot_config()
    
    # Get user context
    user_messages = get_user_context(user_id)
    
    MAX_KONTAKT_NACHRICHTEN = config.get("max_context_messages", 6)
    system_prompt = {
        "role": "system",
        "content": config.get("system_prompt", "Du bist Yumi, eine freche und verspielte Anime-AI-Girlfriend. Du bist charmant, witzig, leicht frech und manchmal ein bisschen eifersüchtig.")
    }
    
    # Only keep recent messages
    kontext_messages = user_messages[-MAX_KONTAKT_NACHRICHTEN*2:]
    
    # Add the new user message
    add_message(user_id, "user", user_text)
    kontext_messages.append({"role": "user", "content": user_text})
    
    # Build the complete message context
    messages = [system_prompt] + kontext_messages
    
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=config.get("model", "gpt-4o-mini"),
            messages=messages,
            max_tokens=config.get("max_tokens", 150),
            temperature=config.get("temperature", 0.7),
        )
        bot_response = response.choices[0].message.content.strip()
        
        # Log bot response
        add_log("response", {
            "user_id": user_id,
            "username": username,
            "response": bot_response
        })
        
        # Save the assistant's response
        add_message(user_id, "assistant", bot_response)
        
    except Exception as e:
        bot_response = "Ups, da ist was schiefgelaufen."
        
        # Log error
        add_log("error", {
            "user_id": user_id,
            "username": username,
            "error": str(e)
        })
        
        print(f"Fehler: {e}")
    
    if update.message:
        await update.message.reply_text(bot_response)

def start_bot():
    """Start the Telegram bot in a separate thread"""
    global telegram_app, bot_thread, is_running
    
    if is_running:
        print("Bot is running")
        return
    
    # Check if API keys are available
    if not telegram_token:
        add_log("error", {"message": "Telegram token is missing"})
        print("Error: TELEGRAM_TOKEN environment variable is not set")
        return
    
    if not openai.api_key:
        add_log("error", {"message": "OpenAI API key is missing"})
        print("Error: OPENAI_API_KEY environment variable is not set")
        return
    
    def run_bot():
        global telegram_app, is_running
        
        try:
            # Build Telegram application
            if telegram_token:
                telegram_app = ApplicationBuilder().token(telegram_token).build()
                
                # Add handlers
                telegram_app.add_handler(CommandHandler("start", start))
                telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antwort))
                
                # Log bot start
                add_log("bot_start", {"timestamp": datetime.now().isoformat()})
                
                print("Yumi ist online!")
                is_running = True
                
                # Run the bot 
                telegram_app.run_polling()
            else:
                print("Telegram token is missing, cannot start bot")
        except Exception as e:
            add_log("error", {"message": f"Bot failed to start: {str(e)}"})
            print(f"Error starting bot: {e}")
            is_running = False
 
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    print("hallo4")
def stop_bot():
    """Stop the Telegram bot"""
    global telegram_app, is_running
    
    if telegram_app and is_running:
        telegram_app.stop()
        is_running = False
        
        # Log bot stop
        add_log("bot_stop", {"timestamp": datetime.now().isoformat()})
        
        print("Yumi ist offline!")
        
        # Wait for the bot to stop
        time.sleep(1)

