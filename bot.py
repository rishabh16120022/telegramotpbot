import logging
import sqlite3
import random
import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time

import config
from database import db
from keyboards import *
import atexit
import signal
import threading

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = telebot.TeleBot(config.BOT_TOKEN)

# Store temporary data
user_states = {}
otp_simulation_threads = {}

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

# ========== OTP SIMULATION SYSTEM ==========
def simulate_otp_delivery(order_id: int, phone_number: str, user_id: int):
    """Simulate OTP delivery in background"""
    try:
        # Wait 10-30 seconds to simulate real OTP delivery
        delay = random.randint(10, 30)
        logger.info(f"Simulating OTP delivery for order {order_id}, delay: {delay}s")
        time.sleep(delay)
        
        # Generate random OTP
        otp_code = str(random.randint(100000, 999999))
        
        # Update database with OTP
        db.update_otp_code(order_id, otp_code)
        
        # Notify user that OTP is ready
        try:
            notification_text = f"""
🔔 *OTP Ready!*

📞 Phone Number: `{phone_number}`
⏰ OTP has arrived and is ready to view.

Click 'View OTP' button to see your OTP code.
            """
            bot.send_message(user_id, notification_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to send OTP notification to user {user_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error in OTP simulation for order {order_id}: {e}")
    finally:
        # Clean up thread tracking
        if order_id in otp_simulation_threads:
            del otp_simulation_threads[order_id]

# ========== UPDATED PURCHASE SYSTEM ==========
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
    account_type = "telegram" if "telegram" in data else "whatsapp"
    
    if user[2] < price:
        bot.answer_callback_query(call.id, f"❌ Need ₹{price}")
        return
    
    # Get available phone number
    phone_number = db.get_available_phone_number(account_type)
    if not phone_number:
        bot.answer_callback_query(call.id, "❌ No accounts available!")
        return
    
    # Deduct balance
    db.update_balance(user_id, -price)
    
    # Create OTP purchase order
    order_id = db.create_otp_purchase(user_id, account_type, phone_number, price)
    
    # Show purchase confirmation with OTP buttons
    purchase_text = f"""
✅ *Purchase Successful!*

📞 Phone Number: `{phone_number}`
💰 Amount Paid: ₹{price}
🆔 Order ID: `{order_id}`

⏳ *OTP Status:* Waiting for OTP...
This may take 10-30 seconds.

Use the buttons below to manage your purchase:
    """
    
    bot.edit_message_text(
        purchase_text,
        call.message.chat.id, call.message.message_id,
        parse_mode='Markdown',
        reply_markup=otp_actions_menu(order_id)
    )
    
    # Start OTP simulation in background
    otp_thread = threading.Thread(
        target=simulate_otp_delivery, 
        args=(order_id, phone_number, user_id),
        daemon=True
    )
    otp_thread.start()
    
    # Track the thread
    otp_simulation_threads[order_id] = otp_thread

# ========== OTP VIEWING & CANCELLATION ==========
def view_otp(call):
    """Show OTP to user"""
    order_id = int(call.data.split('_')[-1])
    order = db.get_order(order_id)
    
    if not order:
        bot.answer_callback_query(call.id, "❌ Order not found!")
        return
    
    order_id, user_id, account_type, phone_number, otp_code, status, price, purchased_at, completed_at, refund = order
    
    if status == 'otp_ready' and otp_code:
        # Show OTP to user
        otp_text = f"""
🔑 *Your OTP Code*

📞 Phone Number: `{phone_number}`
🔑 OTP Code: `{otp_code}`
💰 Amount Paid: ₹{price}

💡 *Instructions:*
1. Open Telegram/WhatsApp
2. Enter phone number: `{phone_number}`
3. Enter OTP code: `{otp_code}`
4. Complete verification

✅ Account will be marked as sold after successful login.
        """
        
        bot.edit_message_text(
            otp_text,
            call.message.chat.id, call.message.message_id,
            parse_mode='Markdown',
            reply_markup=otp_received_menu(order_id)
        )
        
        # Mark order as completed
        db.complete_otp_order(order_id)
        db.mark_phone_sold(phone_number, user_id)
        
    elif status == 'pending':
        # OTP not arrived yet
        bot.answer_callback_query(
            call.id, 
            "⏳ OTP not arrived yet. Please wait...", 
            show_alert=True
        )
    else:
        bot.answer_callback_query(call.id, "❌ No OTP available!")

def cancel_otp_purchase(call):
    """Cancel OTP purchase and refund"""
    order_id = int(call.data.split('_')[-1])
    order = db.get_order(order_id)
    
    if not order:
        bot.answer_callback_query(call.id, "❌ Order not found!")
        return
    
    order_id, user_id, account_type, phone_number, otp_code, status, price, purchased_at, completed_at, refund = order
    
    if status == 'otp_ready':
        # OTP already arrived, cannot cancel
        bot.answer_callback_query(
            call.id, 
            "❌ Cannot cancel! OTP has already arrived.", 
            show_alert=True
        )
        return
    
    if status == 'completed':
        bot.answer_callback_query(
            call.id, 
            "❌ Cannot cancel! Order already completed.", 
            show_alert=True
        )
        return
    
    # Process cancellation and refund
    refund_order = db.cancel_otp_order(order_id)
    
    if refund_order:
        # Release phone number back to pool
        db.release_phone_number(phone_number)
        
        cancel_text = f"""
❌ *Purchase Cancelled*

📞 Phone Number: `{phone_number}`
💰 Refund Amount: ₹{price}
✅ Amount refunded to your wallet.

You can try purchasing another account.
        """
        
        bot.edit_message_text(
            cancel_text,
            call.message.chat.id, call.message.message_id,
            parse_mode='Markdown',
            reply_markup=back_to_main()
        )
        
        # Notify user about refund
        try:
            refund_msg = f"💰 Refund of ₹{price} has been added to your balance."
            bot.send_message(user_id, refund_msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to send refund notification: {e}")
    else:
        bot.answer_callback_query(call.id, "❌ Failed to cancel order!")

# ========== UPDATED BUTTON HANDLER ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data
    
    try:
        # ... (keep all existing button handlers) ...
        
        # OTP viewing and cancellation
        elif data.startswith("view_otp_"):
            view_otp(call)
        elif data.startswith("cancel_otp_"):
            cancel_otp_purchase(call)
        elif data.startswith("confirm_otp_"):
            confirm_otp_received(call)
                
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        bot.answer_callback_query(call.id, "❌ Error occurred!")

def confirm_otp_received(call):
    """Confirm OTP received and mark as completed"""
    order_id = int(call.data.split('_')[-1])
    order = db.get_order(order_id)
    
    if order:
        bot.answer_callback_query(call.id, "✅ OTP confirmed! Thank you.")
        bot.edit_message_text(
            "✅ *OTP Confirmed*\n\nThank you for confirming! Your account is now active.",
            call.message.chat.id, call.message.message_id,
            parse_mode='Markdown',
            reply_markup=back_to_main()
        )

# ========== UPDATED ORDER HISTORY ==========
def view_user_orders(call, user_id):
    orders = db.get_user_orders(user_id)
    active_orders = db.get_user_active_orders(user_id)
    
    if not orders and not active_orders:
        bot.edit_message_text("📭 No orders yet!", call.message.chat.id, call.message.message_id,
                             reply_markup=back_to_main())
        return
    
    orders_text = "📋 *Your Orders*\n\n"
    
    # Show active orders first
    if active_orders:
        orders_text += "🟡 *Active Orders:*\n"
        for order in active_orders[:3]:
            order_id, user_id, account_type, phone_number, otp_code, status, price, purchased_at, completed_at, refund = order
            status_emoji = {'pending': '⏳', 'otp_ready': '🔔'}.get(status, '❓')
            orders_text += f"{status_emoji} {account_type} - ₹{price} - {status}\n"
        orders_text += "\n"
    
    # Show completed orders
    if orders:
        orders_text += "✅ *Completed Orders:*\n"
        for order in orders[:5]:
            order_id, user_id, account_type, phone_number, otp_code, status, price, purchased_at, completed_at, refund = order
            if status in ['completed', 'cancelled']:
                status_emoji = '✅' if status == 'completed' else '❌'
                refund_text = f" (Refund: ₹{refund})" if refund > 0 else ""
                orders_text += f"{status_emoji} {account_type} - ₹{price}{refund_text}\n"
    
    bot.edit_message_text(orders_text, call.message.chat.id, call.message.message_id,
                         reply_markup=back_to_main(), parse_mode='Markdown')

# ... (rest of your existing bot.py code remains the same) ...

#

def exit_handler():
    print("🤖 Bot shutting down...")
    
atexit.register(exit_handler)
signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = telebot.TeleBot(config.BOT_TOKEN)

# Store temporary data
user_states = {}

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
        # Main menu navigation
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
        
        # Owner panel functions
        elif data == "owner_panel":
            if is_owner(user_id):
                show_owner_panel(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        elif data == "manage_admins":
            if is_owner(user_id):
                show_manage_admins(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        elif data == "add_admin":
            if is_owner(user_id):
                start_add_admin(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        elif data == "list_admins":
            if is_owner(user_id):
                show_admin_list(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        elif data.startswith("remove_admin_"):
            if is_owner(user_id):
                remove_admin(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        
        # Account management
        elif data == "owner_account_management":
            if is_owner(user_id):
                show_account_management(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        elif data in ["add_telegram_accounts", "add_whatsapp_accounts"]:
            if is_owner(user_id):
                start_add_accounts(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        elif data == "view_all_accounts":
            if is_owner(user_id):
                show_all_accounts(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        
        # User management
        elif data == "manage_users":
            if is_admin(user_id):
                show_manage_users(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        elif data == "list_all_users":
            if is_admin(user_id):
                show_all_users(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        elif data.startswith("view_user_"):
            if is_admin(user_id):
                show_user_details(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        elif data.startswith("add_balance_") or data.startswith("deduct_balance_"):
            if is_admin(user_id):
                handle_balance_action(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        elif data.startswith("block_user_"):
            if is_admin(user_id):
                block_user(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        elif data.startswith("unblock_user_"):
            if is_admin(user_id):
                unblock_user(call)
            else:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
        
        # Broadcast
        elif data == "broadcast":
            if is_owner(user_id):
                start_broadcast(call)
            else:
                bot.answer_callback_query(call.id, "❌ Owner access required!")
        
        # Purchase handling
        elif data.startswith("buy_"):
            handle_purchase(call, data, user_id)
        
        # Payment approval system
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

# ========== ADMIN MANAGEMENT FUNCTIONS ==========
def show_manage_admins(call):
    bot.edit_message_text("🛡️ *Admin Management*", call.message.chat.id, call.message.message_id,
                         reply_markup=manage_admins_menu(), parse_mode='Markdown')

def start_add_admin(call):
    user_states[call.from_user.id] = 'awaiting_admin_id'
    bot.edit_message_text(
        "👥 *Add New Admin*\n\nSend the user ID you want to make admin:",
        call.message.chat.id, call.message.message_id,
        parse_mode='Markdown',
        reply_markup=back_to_main()
    )

def show_admin_list(call):
    admins = db.get_all_admins()
    if not admins:
        bot.edit_message_text("📝 No admins found.", call.message.chat.id, call.message.message_id,
                             reply_markup=manage_admins_menu())
        return
    
    admin_text = "🛡️ *Current Admins*\n\n"
    for admin in admins:
        user_id, username, is_admin = admin
        status = "👑 Owner" if user_id == config.OWNER_ID else "🛡️ Admin"
        name = f"@{username}" if username else f"User {user_id}"
        admin_text += f"• {name} (`{user_id}`) - {status}\n"
    
    bot.edit_message_text(admin_text, call.message.chat.id, call.message.message_id,
                         parse_mode='Markdown', reply_markup=admin_list_menu(admins))

def remove_admin(call):
    admin_id = int(call.data.split('_')[-1])
    if admin_id == config.OWNER_ID:
        bot.answer_callback_query(call.id, "❌ Cannot remove owner!")
        return
    
    db.remove_admin(admin_id)
    bot.answer_callback_query(call.id, "✅ Admin removed!")
    show_admin_list(call)

# ========== ACCOUNT MANAGEMENT FUNCTIONS ==========
def show_account_management(call):
    accounts_count = db.get_available_accounts_count()
    menu_text = f"""
📱 *Account Management*

📊 *Current Inventory:*
📲 Telegram: {accounts_count.get('telegram', 0)}
💚 WhatsApp: {accounts_count.get('whatsapp', 0)}
    """
    bot.edit_message_text(menu_text, call.message.chat.id, call.message.message_id,
                         reply_markup=owner_account_management(), parse_mode='Markdown')

def start_add_accounts(call):
    account_type = "telegram" if "telegram" in call.data else "whatsapp"
    user_states[call.from_user.id] = f'adding_{account_type}_accounts'
    
    instruction_text = f"""
📝 *Adding {account_type.title()} Accounts*

Send accounts in format:
`phone_number` or `phone_number:otp`

Examples:
`+1234567890`
`+1234567891:123456`

Send /cancel to stop.
    """
    bot.edit_message_text(instruction_text, call.message.chat.id, call.message.message_id,
                         parse_mode='Markdown')

def show_all_accounts(call):
    accounts_count = db.get_available_accounts_count()
    menu_text = f"""
📊 *Account Statistics*

📲 Telegram Available: {accounts_count.get('telegram', 0)}
💚 WhatsApp Available: {accounts_count.get('whatsapp', 0)}
    """
    bot.edit_message_text(menu_text, call.message.chat.id, call.message.message_id,
                         reply_markup=owner_account_management(), parse_mode='Markdown')

# ========== USER MANAGEMENT FUNCTIONS ==========
def show_manage_users(call):
    bot.edit_message_text("👥 *User Management*", call.message.chat.id, call.message.message_id,
                         reply_markup=manage_users_menu(), parse_mode='Markdown')

def show_all_users(call):
    users = db.get_all_users()
    if not users:
        bot.edit_message_text("📝 No users found.", call.message.chat.id, call.message.message_id,
                             reply_markup=manage_users_menu())
        return
    
    users_text = "👥 *All Users*\n\n"
    for user in users[:15]:  # Show first 15 users
        user_id, username, balance, is_blocked, is_admin, joined_date = user
        status = "🚫" if is_blocked else "✅"
        admin_badge = " 🛡️" if is_admin else ""
        name = f"@{username}" if username else f"User {user_id}"
        users_text += f"{status} {name}{admin_badge} - ₹{balance}\n"
    
    bot.edit_message_text(users_text, call.message.chat.id, call.message.message_id,
                         parse_mode='Markdown', reply_markup=all_users_menu(users))

def show_user_details(call):
    user_id = int(call.data.split('_')[-1])
    user = db.get_user(user_id)
    
    if not user:
        bot.answer_callback_query(call.id, "❌ User not found!")
        return
    
    user_id, username, balance, total_spent, accounts_bought, is_blocked, is_admin, joined_date, total_refund = user
    status = "🚫 Blocked" if is_blocked else "✅ Active"
    role = "🛡️ Admin" if is_admin else "👤 User"
    
    user_text = f"""
👤 *User Details*

🆔 User ID: `{user_id}`
👤 Username: @{username if username else 'N/A'}
💰 Balance: ₹{balance}
💳 Total Spent: ₹{total_spent}
📱 Accounts Bought: {accounts_bought}
📊 Status: {status}
🎯 Role: {role}
📅 Joined: {joined_date}
    """
    
    bot.edit_message_text(user_text, call.message.chat.id, call.message.message_id,
                         parse_mode='Markdown', reply_markup=user_actions_menu(user_id))

def handle_balance_action(call):
    data = call.data
    parts = data.split('_')
    action = parts[0]  # add or deduct
    target_user_id = int(parts[2])
    amount = int(parts[3])
    
    target_user = db.get_user(target_user_id)
    if not target_user:
        bot.answer_callback_query(call.id, "❌ User not found!")
        return
    
    if action == "add":
        db.update_balance(target_user_id, amount)
        action_text = "added to"
        emoji = "➕"
    else:  # deduct
        if target_user[2] < amount:
            bot.answer_callback_query(call.id, "❌ User has insufficient balance!", show_alert=True)
            return
        db.update_balance(target_user_id, -amount)
        action_text = "deducted from"
        emoji = "➖"
    
    result_text = f"""
{emoji} *Balance Updated*

💰 Amount: ₹{amount} {action_text} user
👤 User: {target_user[1] or f'User {target_user_id}'}
✅ Operation successful
    """
    
    bot.edit_message_text(result_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    
    # Notify user
    try:
        user_msg = f"💳 Your balance was updated by admin: {emoji} ₹{amount}"
        bot.send_message(target_user_id, user_msg, parse_mode='Markdown')
    except:
        pass

def block_user(call):
    user_id = int(call.data.split('_')[-1])
    db.block_user(user_id)
    bot.answer_callback_query(call.id, "✅ User blocked!")
    show_user_details(call)

def unblock_user(call):
    user_id = int(call.data.split('_')[-1])
    db.unblock_user(user_id)
    bot.answer_callback_query(call.id, "✅ User unblocked!")
    show_user_details(call)

# ========== BROADCAST FUNCTION ==========
def start_broadcast(call):
    user_states[call.from_user.id] = 'awaiting_broadcast'
    bot.edit_message_text(
        "📢 *Broadcast Message*\n\nSend the message you want to broadcast to all users:",
        call.message.chat.id, call.message.message_id,
        parse_mode='Markdown',
        reply_markup=back_to_main()
    )

# ========== PAYMENT APPROVAL SYSTEM ==========
def show_pending_payments(call):
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

# ========== MESSAGE HANDLER FOR TEXT INPUT ==========
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Handle commands
    if text.startswith('/'):
        if text == '/cancel':
            if user_id in user_states:
                del user_states[user_id]
            bot.send_message(message.chat.id, "❌ Operation cancelled.", reply_markup=main_menu())
        return
    
    # Handle admin ID input
    if user_states.get(user_id) == 'awaiting_admin_id':
        if is_owner(user_id):
            try:
                new_admin_id = int(text)
                target_user = db.get_user(new_admin_id)
                if not target_user:
                    db.create_user(new_admin_id, "Unknown")
                
                db.add_admin(new_admin_id)
                del user_states[user_id]
                
                bot.send_message(message.chat.id, f"✅ Admin added: {new_admin_id}", 
                               reply_markup=manage_admins_menu())
                
                # Notify new admin
                try:
                    bot.send_message(new_admin_id, "🎉 You are now an admin!", parse_mode='Markdown')
                except:
                    pass
                    
            except ValueError:
                bot.send_message(message.chat.id, "❌ Invalid user ID! Send numbers only.")
        return
    
    # Handle account addition
    if user_states.get(user_id, '').startswith('adding_'):
        account_type = user_states[user_id].replace('adding_', '').replace('_accounts', '')
        if is_owner(user_id):
            lines = text.split('\n')
            added_count = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    if ':' in line:
                        phone, otp = line.split(':', 1)
                    else:
                        phone, otp = line, None
                    
                    if phone.startswith('+'):
                        price = config.TELEGRAM_OTP_PRICE if account_type == "telegram" else config.WHATSAPP_OTP_PRICE
                        db.add_account(account_type, phone, price, otp)
                        added_count += 1
                except:
                    pass
            
            del user_states[user_id]
            bot.send_message(message.chat.id, f"✅ Added {added_count} {account_type} accounts!",
                           reply_markup=owner_account_management())
        return
    
    # Handle broadcast
    if user_states.get(user_id) == 'awaiting_broadcast':
        if is_owner(user_id):
            users = db.get_all_users()
            success_count = 0
            
            for user in users:
                try:
                    bot.send_message(user[0], f"📢 *Broadcast Message*\n\n{text}", parse_mode='Markdown')
                    success_count += 1
                    time.sleep(0.1)  # Rate limiting
                except:
                    pass
            
            del user_states[user_id]
            bot.send_message(message.chat.id, f"✅ Broadcast sent to {success_count}/{len(users)} users",
                           reply_markup=owner_panel())
        return
    
    # Handle UTR payments (default case)
    parts = text.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        utr_text = ' '.join(parts[:-1])
        amount = int(parts[-1])
    else:
        utr_text = text
        amount = config.MIN_DEPOSIT
    
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


