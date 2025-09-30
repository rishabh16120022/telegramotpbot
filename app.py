from flask import Flask
import threading
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to track bot status
bot_thread = None

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Telegram OTP Bot</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .status { padding: 20px; background: #f0f0f0; border-radius: 10px; }
            </style>
        </head>
        <body>
            <h1>🤖 Telegram OTP Bot</h1>
            <div class="status">
                <p><strong>Status:</strong> ✅ Running</p>
                <p><strong>Service:</strong> Web Service on Render.com</p>
                <p><strong>Health:</strong> <a href="/health">Check Health</a></p>
            </div>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return "OK", 200

@app.route('/start-bot')
def start_bot():
    global bot_thread
    try:
        if bot_thread and bot_thread.is_alive():
            return "Bot is already running", 200
        
        from bot import main as bot_main
        bot_thread = threading.Thread(target=bot_main, daemon=True)
        bot_thread.start()
        return "Bot started successfully", 200
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return f"Error starting bot: {str(e)}", 500

def start_services():
    """Start both Flask app and Telegram bot"""
    try:
        # Start Telegram bot in background thread
        from bot import main as bot_main
        global bot_thread
        bot_thread = threading.Thread(target=bot_main, daemon=True)
        bot_thread.start()
        logger.info("Telegram bot started in background thread")
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")

if __name__ == '__main__':
    # Start the Telegram bot when the app starts
    start_services()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
