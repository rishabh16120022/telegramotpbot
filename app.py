from flask import Flask
import threading
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head><title>Telegram OTP Bot</title></head>
        <body>
            <h1>🤖 Telegram OTP Bot</h1>
            <p><strong>Status:</strong> ✅ Live on Render</p>
            <p><strong>Features:</strong> Payment Approval, User Management, Admin Controls</p>
            <p><a href="/health">Health Check</a></p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return "OK", 200

def start_bot():
    """Start the Telegram bot"""
    try:
        from bot import start_bot
        start_bot()
    except Exception as e:
        logger.error(f"Bot failed: {e}")

if __name__ == '__main__':
    # Start bot in background thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting web service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
