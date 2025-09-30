from flask import Flask
import threading
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

bot_thread = None
bot_running = False

@app.route('/')
def home():
    return """
    <html>
        <head><title>Telegram OTP Bot</title></head>
        <body>
            <h1>🤖 Telegram OTP Bot</h1>
            <p><strong>Status:</strong> ✅ Live</p>
            <p><strong>Service:</strong> Render.com</p>
            <p><a href="/health">Health Check</a></p>
            <p>Bot should be running automatically.</p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return "OK", 200

@app.route('/logs')
def show_logs():
    return "Bot logs would appear here", 200

def start_bot():
    """Start the Telegram bot"""
    global bot_running
    try:
        logger.info("🚀 Starting Telegram Bot...")
        from bot import main as bot_main
        bot_main()
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        bot_running = False

def start_bot_in_thread():
    """Start bot in a separate thread"""
    global bot_thread, bot_running
    try:
        if bot_thread and bot_thread.is_alive():
            logger.info("Bot already running")
            return
            
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        bot_running = True
        logger.info("✅ Bot thread started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start bot thread: {e}")

# Start bot when app starts
@app.before_first_request
def startup():
    logger.info("🔧 Starting up application...")
    time.sleep(5)  # Wait for everything to initialize
    start_bot_in_thread()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Starting Flask app on port {port}")
    
    # Start bot in background
    startup_thread = threading.Thread(target=startup, daemon=True)
    startup_thread.start()
    
    app.run(host='0.0.0.0', port=port, debug=False)
