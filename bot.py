import logging
import sqlite3
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler, 
    Filters, CallbackContext, ConversationHandler
)

import config
from database import db
from keyboards import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
AWAITING_ADMIN_ID, AWAITING_ACCOUNTS, AWAITING_BROADCAST, AWAITING_UTR = range(4)

# Authentication functions
def is_owner(user_id: int) -> bool:
    return user_id == config.OWNER_ID

def is_admin(user_id: int) -> bool:
    if is_owner(user_id):
        return True
    if user_id in config.ADMIN_IDS:
        return True
    user = db.get_user(user_id)
    return user and user[6]

# ========== COMMAND HANDLERS ==========
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    db.create_user(user_id, username)
    
    accounts_count = db.get_available_accounts_count()
    telegram_count = accounts_count.get('telegram', 0)
    whatsapp_count = accounts_count.get('whatsapp', 0)
    
    welcome_message = f"""
🌟 *Welcome to Account Store Bot!* 🌟

📊 *Available Accounts:*
📲 Telegram Accounts: {telegram_count}
💚 WhatsApp Accounts: {whatsapp_count}

💎 *Features:*
• Buy OTP for Telegram & WhatsApp
• Purchase ready sessions
• Instant delivery
• 24/7 support

Use the buttons below to get started! 🚀
    """
    
    update.message.reply_text(welcome_message, reply_markup=main_menu(), parse_mode='Markdown')

def help_command(update: Update, context: CallbackContext):
    help_text = """
🆘 *Help Menu* 🆘

*Commands:*
/start - Start bot
/help - Show help
/stats - Your statistics  
/balance - Check balance

*Minimum Deposit:* ₹50
    """
    update.message.reply_text(help_text, parse_mode='Markdown')

def stats_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        stats_text = f"""
📊 *Your Statistics*

👤 User ID: `{user[0]}`
💰 Balance: ₹{user[2]}
💳 Total Spent: ₹{user[3]}
📱 Accounts Bought: {user[4]}
        """
        update.message.reply_text(stats_text, parse_mode='Markdown')
    else:
        update.message.reply_text("❌ User not found!")

def balance_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        update.message.reply_text(f"💳 *Balance:* ₹{user[2]}", parse_mode='Markdown')
    else:
        update.message.reply_text("❌ User not found!")

# ========== BUTTON HANDLER ==========
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    try:
        if data == "main_menu":
            show_main_menu(query)
        elif data == "buy_otp":
            show_otp_menu(query)
        elif data == "buy_session":
            show_session_menu(query)
        elif data == "deposit":
            show_deposit_menu(query)
        elif data == "stats":
            show_user_stats(query, user_id)
        elif data == "my_orders":
            view_user_orders(query, user_id)
        elif data == "show_qr":
            show_qr_code(query)
        elif data == "owner_panel":
            if is_owner(user_id):
                show_owner_panel(query)
            else:
                query.edit_message_text("❌ Owner access required!")
        elif data.startswith("buy_"):
            handle_purchase(query, data, user_id, context)
                
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        query.edit_message_text("❌ An error occurred. Please try again.")

# ========== MENU FUNCTIONS ==========
def show_main_menu(query):
    accounts_count = db.get_available_accounts_count()
    telegram_count = accounts_count.get('telegram', 0)
    whatsapp_count = accounts_count.get('whatsapp', 0)
    
    menu_text = f"""
🏠 *Main Menu*

📊 *Available Accounts:*
📲 Telegram: {telegram_count}
💚 WhatsApp: {whatsapp_count}
    """
    query.edit_message_text(menu_text, reply_markup=main_menu(), parse_mode='Markdown')

def show_otp_menu(query):
    menu_text = """
📱 *Buy OTP*

• Telegram OTP - ₹10
• WhatsApp OTP - ₹15
    """
    query.edit_message_text(menu_text, reply_markup=buy_otp_menu(), parse_mode='Markdown')

def show_session_menu(query):
    menu_text = """
💳 *Buy Session*

• Telegram Session - ₹25
• WhatsApp Session - ₹25
    """
    query.edit_message_text(menu_text, reply_markup=buy_session_menu(), parse_mode='Markdown')

def show_deposit_menu(query):
    menu_text = f"""
💰 *Deposit Funds*

💳 *Minimum Deposit:* ₹{config.MIN_DEPOSIT}
    """
    query.edit_message_text(menu_text, reply_markup=deposit_menu(), parse_mode='Markdown')

def show_user_stats(query, user_id):
    user = db.get_user(user_id)
    if user:
        stats_text = f"""
📊 *Your Statistics*

👤 User ID: `{user[0]}`
💰 Balance: ₹{user[2]}
📱 Accounts Bought: {user[4]}
        """
        query.edit_message_text(stats_text, reply_markup=back_to_main(), parse_mode='Markdown')

def show_qr_code(query):
    qr_text = f"""
📱 *Payment QR Code*

{config.OWNER_QR_CODE}

Send UTR after payment.
    """
    query.edit_message_text(qr_text, reply_markup=back_to_main(), parse_mode='Markdown')

def show_owner_panel(query):
    query.edit_message_text("👑 *Owner Panel*", reply_markup=owner_panel(), parse_mode='Markdown')

# ========== PURCHASE SYSTEM ==========
def handle_purchase(query, data, user_id, context: CallbackContext):
    user = db.get_user(user_id)
    
    if user and user[5]:
        query.edit_message_text("❌ Account blocked!", reply_markup=back_to_main())
        return
    
    prices = {
        "buy_telegram_otp": config.TELEGRAM_OTP_PRICE,
        "buy_whatsapp_otp": config.WHATSAPP_OTP_PRICE,
        "buy_telegram_session": config.SESSION_PRICE,
        "buy_whatsapp_session": config.SESSION_PRICE
    }
    
    price = prices.get(data, 0)
    
    if user[2] < price:
        query.edit_message_text(f"❌ Need ₹{price}", reply_markup=back_to_main())
        return
    
    account_type = "telegram" if "telegram" in data else "whatsapp"
    account = db.get_available_account(account_type)
    
    if not account:
        query.edit_message_text("❌ No accounts!", reply_markup=back_to_main())
        return
    
    # Simulate purchase
    db.update_balance(user_id, -price)
    success_text = f"""
✅ *Purchase Successful!*

💰 Paid: ₹{price}
📞 Number: `{account[2]}`
    """
    query.edit_message_text(success_text, parse_mode='Markdown', reply_markup=back_to_main())

def view_user_orders(query, user_id):
    orders = db.get_user_orders(user_id)
    if not orders:
        query.edit_message_text("📭 No orders!", reply_markup=back_to_main())
        return
    
    orders_text = "📋 *Your Orders:*\n\n"
    for order in orders[:3]:
        orders_text += f"• {order[3]} - ₹{order[6]}\n"
    
    query.edit_message_text(orders_text, parse_mode='Markdown', reply_markup=back_to_main())

# ========== UTR HANDLING ==========
def handle_utr(update: Update, context: CallbackContext):
    utr = update.message.text
    user_id = update.effective_user.id
    
    if len(utr) < 10:
        update.message.reply_text("❌ Invalid UTR!")
        return
    
    message = f"💰 Payment\nUser: {user_id}\nUTR: {utr}"
    
    # Notify admins
    admins = db.get_all_admins()
    for admin in admins:
        try:
            context.bot.send_message(admin[0], message)
        except:
            pass
    
    update.message.reply_text("✅ UTR received!", reply_markup=back_to_main())

# ========== MAIN FUNCTION ==========
def main():
    logger.info("🚀 Starting Telegram Bot...")
    
    # Create updater
    updater = Updater(token=config.BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("stats", stats_command))
    dispatcher.add_handler(CommandHandler("balance", balance_command))
    dispatcher.add_handler(CommandHandler("mybalance", balance_command))
    
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_utr))
    
    # Start polling
    logger.info("🤖 Bot is now running...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
