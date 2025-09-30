from flask import Flask
import threading
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to track if the bot has been started
bot_started = False

@app.route('/')
def home():
    return "Telegram Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

def start_bot():
    """Function to start the bot"""
    try:
        from bot import main
        main()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    # Start the bot in a background thread only if it hasn't been started
    global bot_started
    if not bot_started:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        bot_started = True
        logger.info("Bot thread started.")
    else:
        logger.info("Bot already started.")

    # Start the Flask app
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
