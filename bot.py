import logging
import sqlite3
import random
import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

import config
from database import db
from keyboards import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = telebot.TeleBot(config.BOT_TOKEN)

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
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
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
    
    bot.send_message(message.chat.id, welcome_message, reply_markup=main_menu(), parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🆘 *Help Menu* 🆘

*Commands:*
/start - Start bot
/help - Show help
/stats - Your statistics  
/balance - Check balance

*Features:*
📱 Buy OTP - Purchase OTP for accounts
💳 Buy Session - Buy ready sessions  
💰 Deposit - Add funds to wallet

*Minimum Deposit:* ₹50
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if user:
        stats_text = f"""
📊 *Your Statistics*

👤 User ID: `{user[0]}`
💰 Balance: ₹{user[2]}
💳 Total Spent: ₹{user[3]}
📱 Accounts Bought: {user[4]}
        """
        bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ User not found!")

@bot.message_handler(commands=['balance', 'mybalance'])
def balance_command(message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if user:
        bot.send_message(message.chat.id, f"💳 *Your Balance:* ₹{user[2]}", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "❌ User not found!")

# ========== BUTTON HANDLERS ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data
    
    try:
        if data == "main_menu":
            show_main_menu(call)
        elif data == "buy_otp":
            show_otp_menu(call)
        elif data == "buy_session":
            show_session_menu(call)
        elif data == "deposit":
            show_deposit_menu(call)
        elif data == "stats":
            show_user_stats(call, user_id)
        elif data == "my_orders":
            view_user_orders(call, user_id)
        elif data == "show_qr":
            show_qr_code(call)
        elif data == "owner_panel":
            if is_owner(user_id):
                show_owner_panel(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        elif data == "pending_payments":
            if is_admin(user_id):
                show_pending_payments(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        elif data.startswith("view_payment_"):
            if is_admin(user_id):
                view_payment_details(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        elif data.startswith("approve_payment_"):
            if is_admin(user_id):
                approve_payment(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        elif data.startswith("decline_payment_"):
            if is_admin(user_id):
                decline_payment(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        elif data.startswith("buy_"):
            handle_purchase(call, data, user_id)
                
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

# ========== MENU FUNCTIONS ==========
def show_main_menu(call):
    accounts_count = db.get_available_accounts_count()
    telegram_count = accounts_count.get('telegram', 0)
    whatsapp_count = accounts_count.get('whatsapp', 0)
    
    menu_text = f"""
🏠 *Main Menu*

📊 *Available Accounts:*
📲 Telegram: {telegram_count}
💚 WhatsApp: {whatsapp_count}
    """
    bot.edit_message_text(menu_text, call.message.chat.id, call.message.message_id, 
                         reply_markup=main_menu(), parse_mode='Markdown')

def show_otp_menu(call):
    menu_text = """
📱 *Buy OTP*

• Telegram OTP - ₹10
• WhatsApp OTP - ₹15
    """
    bot.edit_message_text(menu_text, call.message.chat.id, call.message.message_id,
                         reply_markup=buy_otp_menu(), parse_mode='Markdown')

def show_session_menu(call):
    menu_text = """
💳 *Buy Session*

• Telegram Session - ₹25
• WhatsApp Session - ₹25
    """
    bot.edit_message_text(menu_text, call.message.chat.id, call.message.message_id,
                         reply_markup=buy_session_menu(), parse_mode='Markdown')

def show_deposit_menu(call):
    menu_text = f"""
💰 *Deposit Funds*

💳 *Minimum Deposit:* ₹{config.MIN_DEPOSIT}
    """
    bot.edit_message_text(menu_text, call.message.chat.id, call.message.message_id,
                         reply_markup=deposit_menu(), parse_mode='Markdown')

def show_user_stats(call, user_id):
    user = db.get_user(user_id)
    if user:
        stats_text = f"""
📊 *Your Statistics*

👤 User ID: `{user[0]}`
💰 Balance: ₹{user[2]}
📱 Accounts Bought: {user[4]}
        """
        bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id,
                             reply_markup=back_to_main(), parse_mode='Markdown')

def show_qr_code(call):
    qr_text = f"""
📱 *Payment QR Code*

{config.OWNER_QR_CODE}

*After payment, send UTR number to admin.*
    """
    bot.edit_message_text(qr_text, call.message.chat.id, call.message.message_id,
                         reply_markup=back_to_main(), parse_mode='Markdown')

def show_owner_panel(call):
    bot.edit_message_text("👑 *Owner Panel*", call.message.chat.id, call.message.message_id,
                         reply_markup=owner_panel(), parse_mode='Markdown')

# ========== PAYMENT APPROVAL SYSTEM ==========
def show_pending_payments(call):
    """Show all pending payments to admin/owner"""
    pending_payments = db.get_pending_payments()
    
    if not pending_payments:
        bot.edit_message_text(
            "⏳ *No Pending Payments*",
            call.message.chat.id, call.message.message_id,
            parse_mode='Markdown',
            reply_markup=back_to_main()
        )
        return
    
    payments_text = "⏳ *Pending Payment Requests*\n\n"
    
    for payment in pending_payments[:10]:
        payment_id, user_id, amount, utr, status, admin_id, created_at, username = payment
        user_display = f"@{username}" if username else f"User {user_id}"
        payments_text += f"💰 *Payment #{payment_id}*\n"
        payments_text += f"👤 {user_display}\n"
        payments_text += f"💳 Amount: ₹{amount}\n"
        payments_text += f"🔢 UTR: `{utr}`\n\n"
    
    bot.edit_message_text(
        payments_text,
        call.message.chat.id, call.message.message_id,
        parse_mode='Markdown',
        reply_markup=pending_payments_menu(pending_payments)
    )

def view_payment_details(call):
    """Show details of a specific payment"""
    payment_id = int(call.data.split('_')[-1])
    payment = db.get_payment(payment_id)
    
    if not payment:
        bot.answer_callback_query(call.id, "❌ Payment not found!")
        return
    
    payment_id, user_id, amount, utr, status, admin_id, created_at, username = payment
    user_display = f"@{username}" if username else f"User {user_id}"
    
    payment_text = f"""
💰 *Payment Details - #{payment_id}*

👤 *User:* {user_display}
🆔 User ID: `{user_id}`
💳 *Amount:* ₹{amount}
🔢 *UTR:* `{utr}`
📅 *Submitted:* {created_at}

Choose an action:
"""
    
    bot.edit_message_text(
        payment_text,
        call.message.chat.id, call.message.message_id,
        parse_mode='Markdown',
        reply_markup=payment_actions_menu(payment_id)
    )

def approve_payment(call):
    """Approve a payment request"""
    payment_id = int(call.data.split('_')[-1])
    payment = db.approve_payment(payment_id, call.from_user.id)
    
    if payment:
        target_user_id, amount = payment
        
        # Notify the user
        try:
            user_notification = f"""
✅ *Payment Approved!*

Your payment of ₹{amount} has been approved and added to your balance.

Thank you for your payment! 🎉
"""
            bot.send_message(target_user_id, user_notification, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
        
        success_text = f"""
✅ *Payment Approved!*

💰 Amount: ₹{amount}
👤 User ID: `{target_user_id}`
✅ Balance has been added to user's account.
"""
        bot.edit_message_text(success_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        
    else:
        bot.answer_callback_query(call.id, "❌ Payment not found!")

def decline_payment(call):
    """Decline a payment request"""
    payment_id = int(call.data.split('_')[-1])
    payment = db.get_payment(payment_id)
    
    if payment and payment[4] == 'pending':
        db.decline_payment(payment_id, call.from_user.id)
        target_user_id = payment[1]
        amount = payment[2]
        
        # Notify the user
        try:
            user_notification = f"""
❌ *Payment Declined*

Your payment of ₹{amount} has been declined.

Please contact admin if you believe this is a mistake.
"""
            bot.send_message(target_user_id, user_notification, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
        
        decline_text = f"""
❌ *Payment Declined*

💰 Amount: ₹{amount}
👤 User ID: `{target_user_id}`
❌ Payment request has been declined.
"""
        bot.edit_message_text(decline_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    else:
        bot.answer_callback_query(call.id, "❌ Payment not found!")

# ========== PURCHASE SYSTEM ==========
def handle_purchase(call, data, user_id):
    user = db.get_user(user_id)
    
    if user and user[5]:
        bot.answer_callback_query(call.id, "❌ Account blocked!")
        return
    
    prices = {
        "buy_telegram_otp": config.TELEGRAM_OTP_PRICE,
        "buy_whatsapp_otp": config.WHATSAPP_OTP_PRICE,
        "buy_telegram_session": config.SESSION_PRICE,
        "buy_whatsapp_session": config.SESSION_PRICE
    }
    
    price = prices.get(data, 0)
    
    if user[2] < price:
        bot.answer_callback_query(call.id, f"❌ Need ₹{price}")
        return
    
    account_type = "telegram" if "telegram" in data else "whatsapp"
    account = db.get_available_account(account_type)
    
    if not account:
        bot.answer_callback_query(call.id, "❌ No accounts available!")
        return
    
    # Process purchase
    db.update_balance(user_id, -price)
    
    # Simulate OTP delivery
    otp_code = str(random.randint(100000, 999999))
    
    success_text = f"""
✅ *Purchase Successful!*

📞 Number: `{account[2]}`
🔑 OTP: `{otp_code}`
💰 Paid: ₹{price}

Thank you for your purchase! 🎉
    """
    
    bot.edit_message_text(success_text, call.message.chat.id, call.message.message_id,
                         parse_mode='Markdown')
    
    # Mark account as sold
    db.mark_account_sold(account[0], user_id)

def view_user_orders(call, user_id):
    orders = db.get_user_orders(user_id)
    if not orders:
        bot.edit_message_text("📭 No orders yet!", call.message.chat.id, call.message.message_id,
                             reply_markup=back_to_main())
        return
    
    orders_text = "📋 *Your Orders:*\n\n"
    for order in orders[:5]:
        status_emoji = {'success': '✅', 'failed': '❌', 'cancelled': '🔄', 'pending': '⏳'}.get(order[5], '❓')
        orders_text += f"{status_emoji} {order[3]} - ₹{order[6]} - {order[5]}\n"
    
    bot.edit_message_text(orders_text, call.message.chat.id, call.message.message_id,
                         reply_markup=back_to_main(), parse_mode='Markdown')

# ========== UTR HANDLING ==========
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        return
    
    # Assume it's a UTR number
    utr = message.text.strip()
    user_id = message.from_user.id
    
    # Check if message contains amount (format: "UTR123456 500")
    parts = utr.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        utr_text = ' '.join(parts[:-1])
        amount = int(parts[-1])
    else:
        utr_text = utr
        amount = config.MIN_DEPOSIT
    
    # Validate amount
    if amount < config.MIN_DEPOSIT:
        amount = config.MIN_DEPOSIT
    
    if len(utr_text) < 10:
        bot.send_message(message.chat.id, 
                        "❌ Invalid UTR format! Send: `UTR1234567890 500`",
                        parse_mode='Markdown',
                        reply_markup=back_to_main())
        return
    
    # Create payment request
    payment_id = db.create_payment_request(user_id, amount, utr_text)
    
    # Notify all admins
    admins = db.get_all_admins()
    admin_message = f"""
💰 *New Payment Request - #{payment_id}*

👤 User: {message.from_user.username or 'N/A'} (ID: `{user_id}`)
💳 Amount: ₹{amount}
🔢 UTR: `{utr_text}`
📅 Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Click below to review this payment.
"""
    
    for admin in admins:
        try:
            keyboard = [[InlineKeyboardButton("👀 Review Payment", callback_data=f"view_payment_{payment_id}")]]
            bot.send_message(
                admin[0], 
                admin_message, 
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin[0]}: {e}")
    
    # Confirm to user
    user_message = f"""
✅ *Payment Request Submitted!*

💰 Amount: ₹{amount}
🔢 Your UTR: `{utr_text}`
📊 Payment ID: `{payment_id}`

Your payment is under review. You'll be notified once approved.
"""
    
    bot.send_message(message.chat.id, user_message, parse_mode='Markdown', reply_markup=back_to_main())

# ========== START BOT ==========
def start_bot():
    logger.info("🚀 Starting Telegram Bot...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == '__main__':
    start_bot()
