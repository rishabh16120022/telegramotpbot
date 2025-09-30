# Telegram OTP Bot

Complete Telegram bot for selling OTP services deployed on Render.com.

## Features
- Buy Telegram/WhatsApp OTP & Sessions
- Automatic refund system
- Admin management
- Payment approval system
- User management

## Deployment on Render.com

1. **Create Web Service** on Render
2. **Connect GitHub repository**
3. **Set Environment Variables:**
   - `BOT_TOKEN`: From BotFather
   - `OWNER_ID`: Your Telegram user ID
4. **Deploy**

## Environment Variables
- `BOT_TOKEN`: Telegram bot token
- `OWNER_ID`: Your user ID
- `ADMIN_IDS`: Comma-separated admin IDs
- `OWNER_QR_CODE`: Your payment QR code URL

## Access
- Web Interface: `https://your-app.onrender.com`
- Health Check: `https://your-app.onrender.com/health`
