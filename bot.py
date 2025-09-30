import logging
import sqlite3
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Import your modules
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

# Health check server for Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            try:
                # Test database connection
                conn = sqlite3.connect(config.DB_PATH)
                conn.close()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    port = config.PORT
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()

# Start health server in background thread
if os.environ.get('RENDER', False):
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

# Authentication functions
def is_owner(user_id: int) -> bool:
    return user_id == config.OWNER_ID

def is_admin(user_id: int) -> bool:
    if is_owner(user_id):
        return True
    if user_id in config.ADMIN_IDS:
        return True
    user = db.get_user(user_id)
    return user and user[6]  # is_admin field

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Create user if not exists
    db.create_user(user_id, username)
    
    # Get available accounts count
    accounts_count = db.get_available_accounts_count()
    telegram_count = accounts_count.get('telegram', 0)
    whatsapp_count = accounts_count.get('whatsapp', 0)
    
    welcome_message = f"""
🌟 *Welcome to Account Store Bot!* 🌟

🤖 *Your one-stop solution for Telegram & WhatsApp accounts*

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
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=main_menu(),
        parse_mode='Markdown'
    )

# Help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆘 *Help Menu* 🆘

*Available Commands:*
/start - Start the bot
/help - Show this help message
/stats - Show your statistics
/balance - Check your balance
/mybalance - Check your balance

*Button Functions:*
📱 *Buy OTP* - Purchase OTP for accounts
💳 *Buy Session* - Buy ready sessions  
💰 *Deposit* - Add funds to your wallet
📊 *Stats* - View your statistics
📋 *My Orders* - View your order history

*Minimum Deposit:* ₹50

*Support:* Contact @owner_username for assistance
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Stats command handler
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        stats_text = f"""
📊 *Your Statistics* 📊

👤 User ID: `{user[0]}`
💰 Balance: ₹{user[2]}
💳 Total Spent: ₹{user[3]}
📱 Accounts Bought: {user[4]}
🔄 Total Refunds: ₹{user[8] if len(user) > 8 else 0}
📅 Member Since: {user[7]}
        """
        await update.message.reply_text(stats_text, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ User not found!")

# Balance command handler
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        balance_text = f"""
💳 *Your Balance* 💳

💰 Available Balance: *₹{user[2]}*
        """
        await update.message.reply_text(balance_text, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ User not found!")

# Main button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    try:
        # Main menu navigation
        if data == "main_menu":
            await show_main_menu(query)
        elif data == "buy_otp":
            await show_otp_menu(query)
        elif data == "buy_session":
            await show_session_menu(query)
        elif data == "deposit":
            await show_deposit_menu(query)
        elif data == "stats":
            await show_user_stats(query, user_id)
        elif data == "my_orders":
            await view_user_orders(query, user_id)
        
        # Owner panel
        elif data == "owner_panel":
            if is_owner(user_id):
                await show_owner_panel(query)
            else:
                await query.edit_message_text("❌ Owner access required!")
        elif data == "manage_admins":
            if is_owner(user_id):
                await manage_admins(query)
            else:
                await query.edit_message_text("❌ Owner access required!")
        elif data == "add_admin":
            if is_owner(user_id):
                await add_admin_handler(query, context)
            else:
                await query.edit_message_text("❌ Owner access required!")
        elif data == "list_admins":
            if is_owner(user_id):
                await list_admins_handler(query)
            else:
                await query.edit_message_text("❌ Owner access required!")
        
        # Account management
        elif data == "owner_account_management":
            if is_owner(user_id):
                await show_account_management(query)
            else:
                await query.edit_message_text("❌ Owner access required!")
        elif data in ["add_telegram_accounts", "add_whatsapp_accounts"]:
            if is_owner(user_id):
                await add_accounts(query, context)
            else:
                await query.edit_message_text("❌ Owner access required!")
        elif data == "view_all_accounts":
            if is_owner(user_id):
                await view_all_accounts(query)
            else:
                await query.edit_message_text("❌ Owner access required!")
        
        # Purchase handling
        elif data.startswith("buy_"):
            await handle_purchase(query, data, user_id, context)
        elif data.startswith("cancel_order_"):
            await cancel_order(query, context)
        
        # Payment approval
        elif data == "pending_payments":
            if is_admin(user_id):
                await show_pending_payments(query)
            else:
                await query.edit_message_text("❌ Admin access required!")
        elif data.startswith("approve_payment_") or data.startswith("decline_payment_"):
            if is_admin(user_id):
                await handle_payment_approval(query, data, user_id)
            else:
                await query.edit_message_text("❌ Admin access required!")
        
        # Admin management
        elif data.startswith("remove_admin_confirm_"):
            if is_owner(user_id):
                await remove_admin_confirm(query)
            else:
                await query.edit_message_text("❌ Owner access required!")
        elif data.startswith("remove_admin_final_"):
            if is_owner(user_id):
                await remove_admin_final(query, context)
            else:
                await query.edit_message_text("❌ Owner access required!")
        
        # User management
        elif data == "manage_users":
            if is_admin(user_id):
                await manage_users(query)
            else:
                await query.edit_message_text("❌ Admin access required!")
        elif data == "list_all_users":
            if is_admin(user_id):
                await list_all_users(query, context)
            else:
                await query.edit_message_text("❌ Admin access required!")
        
        # Broadcast
        elif data == "broadcast":
            if is_owner(user_id):
                await start_broadcast(query, context)
            else:
                await query.edit_message_text("❌ Owner access required!")
                
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")

# Menu display functions
async def show_main_menu(query):
    accounts_count = db.get_available_accounts_count()
    telegram_count = accounts_count.get('telegram', 0)
    whatsapp_count = accounts_count.get('whatsapp', 0)
    
    menu_text = f"""
🏠 *Main Menu*

📊 *Available Accounts:*
📲 Telegram: {telegram_count}
💚 WhatsApp: {whatsapp_count}

Choose an option below:
    """
    
    await query.edit_message_text(menu_text, reply_markup=main_menu(), parse_mode='Markdown')

async def show_otp_menu(query):
    menu_text = """
📱 *Buy OTP*

Choose account type:
• Telegram OTP - ₹10
• WhatsApp OTP - ₹15

Select an option:
    """
    await query.edit_message_text(menu_text, reply_markup=buy_otp_menu(), parse_mode='Markdown')

async def show_session_menu(query):
    menu_text = """
💳 *Buy Session*

Choose session type:
• Telegram Session - ₹25
• WhatsApp Session - ₹25

Select an option:
    """
    await query.edit_message_text(menu_text, reply_markup=buy_session_menu(), parse_mode='Markdown')

async def show_deposit_menu(query):
    menu_text = f"""
💰 *Deposit Funds*

💳 *Minimum Deposit:* ₹{config.MIN_DEPOSIT}

Click the button below to see QR code for payment.

*After payment, send the UTR number to @owner_username for verification.*
    """
    await query.edit_message_text(menu_text, reply_markup=deposit_menu(), parse_mode='Markdown')

async def show_user_stats(query, user_id):
    user = db.get_user(user_id)
    if user:
        stats_text = f"""
📊 *Your Statistics*

👤 User ID: `{user[0]}`
💰 Balance: ₹{user[2]}
💳 Total Spent: ₹{user[3]}
📱 Accounts Bought: {user[4]}
📅 Member Since: {user[7]}
        """
        await query.edit_message_text(stats_text, reply_markup=back_to_main(), parse_mode='Markdown')

# Purchase handling with refund system
async def handle_purchase(query, data, user_id, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(user_id)
    
    if user and user[5]:  # Check if blocked
        await query.edit_message_text("❌ Your account is blocked! Contact admin.", reply_markup=back_to_main())
        return
    
    prices = {
        "buy_telegram_otp": config.TELEGRAM_OTP_PRICE,
        "buy_whatsapp_otp": config.WHATSAPP_OTP_PRICE,
        "buy_telegram_session": config.SESSION_PRICE,
        "buy_whatsapp_session": config.SESSION_PRICE
    }
    
    account_types = {
        "buy_telegram_otp": "telegram",
        "buy_whatsapp_otp": "whatsapp",
        "buy_telegram_session": "telegram_session",
        "buy_whatsapp_session": "whatsapp_session"
    }
    
    price = prices.get(data)
    account_type = account_types.get(data)
    
    if user[2] < price:
        await query.edit_message_text(
            f"❌ Insufficient balance! You need ₹{price}\n\n💰 Your balance: ₹{user[2]}",
            reply_markup=back_to_main()
        )
        return
    
    # Get available account
    account = db.get_available_account(account_type.replace('_session', ''))
    if not account:
        await query.edit_message_text("❌ Sorry, no accounts available at the moment!", reply_markup=back_to_main())
        return
    
    # Create order and deduct balance
    order_id = db.create_order(user_id, account_type, account[2], None, price)
    db.update_balance(user_id, -price)
    
    # Show purchase in progress
    progress_text = f"""
🔄 *Purchase In Progress...*

📦 *Account Details:*
📱 Type: {account_type.replace('_', ' ').title()}
📞 Number: `{account[2]}`
💰 Amount: ₹{price}

⏳ Please wait while we process your order...
This may take 10-30 seconds.
    """
    
    keyboard = [
        [InlineKeyboardButton("❌ Cancel Order & Refund", callback_data=f"cancel_order_{order_id}")],
        [InlineKeyboardButton("🔄 Refresh Status", callback_data=f"refresh_order_{order_id}")]
    ]
    
    await query.edit_message_text(progress_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Process OTP delivery in background
    asyncio.create_task(process_otp_delivery(context, order_id, account[0], user_id))

async def process_otp_delivery(context: ContextTypes.DEFAULT_TYPE, order_id: int, account_id: int, user_id: int):
    """Process OTP delivery with refund system"""
    import random
    await asyncio.sleep(random.randint(5, 15))  # Simulate OTP delivery
    
    order = db.get_order(order_id)
    if order and order[5] == 'pending':  # status
        # 90% success rate simulation
        if random.random() < 0.9:
            # OTP delivered successfully
            otp_code = str(random.randint(100000, 999999))
            db.complete_order(order_id, 'success', otp_code)
            db.mark_account_sold(account_id, user_id)
            
            success_text = f"""
✅ *Order Completed Successfully!*

📦 *Account Details:*
📞 Number: `{order[4]}`
🔑 OTP Code: `{otp_code}`
💰 Amount Paid: ₹{order[6]}

💡 *Instructions:*
1. Use this number in Telegram/WhatsApp
2. Enter the OTP when prompted
3. Complete verification

Thank you for your purchase! 🎉
            """
            
            try:
                await context.bot.send_message(user_id, success_text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to send success message to user {user_id}: {e}")
        else:
            # OTP delivery failed - automatic refund
            db.complete_order(order_id, 'failed')
            db.update_balance(user_id, order[6])  # Refund full amount
            db.update_user_refund(user_id, order[6])
            
            fail_text = f"""
❌ *OTP Delivery Failed*

We couldn't receive the OTP for the number `{order[4]}`.

💰 *Refund Issued:* ₹{order[6]}
💳 *Your balance has been refunded.*

Please try with another number or contact support if the issue persists.
            """
            
            try:
                await context.bot.send_message(user_id, fail_text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to send fail message to user {user_id}: {e}")

async def cancel_order(query, context: ContextTypes.DEFAULT_TYPE):
    """Cancel order and issue refund"""
    order_id = int(query.data.split('_')[-1])
    order = db.get_order(order_id)
    
    if not order:
        await query.edit_message_text("❌ Order not found!", reply_markup=back_to_main())
        return
    
    user_id = query.from_user.id
    if order[1] != user_id:
        await query.edit_message_text("❌ You can only cancel your own orders!", reply_markup=back_to_main())
        return
    
    if order[5] != 'pending':
        await query.edit_message_text("❌ This order cannot be cancelled anymore!", reply_markup=back_to_main())
        return
    
    # Process cancellation and refund
    db.complete_order(order_id, 'cancelled')
    db.update_balance(user_id, order[6])
    db.update_user_refund(user_id, order[6])
    
    cancel_text = f"""
❌ *Order Cancelled*

Your order for `{order[4]}` has been cancelled.

💰 *Refund Issued:* ₹{order[6]}
💳 *Amount has been added back to your balance.*

You can try purchasing another account.
    """
    
    await query.edit_message_text(cancel_text, parse_mode='Markdown', reply_markup=back_to_main())

# Owner panel functions
async def show_owner_panel(query):
    owner_text = """
👑 *Owner Panel*

Manage your bot and users:
• Manage Users & Admins
• View all statistics
• Send broadcast messages
• Approve pending payments
• Manage accounts inventory
    """
    await query.edit_message_text(owner_text, reply_markup=owner_panel(), parse_mode='Markdown')

async def show_account_management(query):
    accounts_count = db.get_available_accounts_count()
    telegram_count = accounts_count.get('telegram', 0)
    whatsapp_count = accounts_count.get('whatsapp', 0)
    
    menu_text = f"""
📱 *Account Management*

📊 *Current Inventory:*
📲 Telegram: {telegram_count}
💚 WhatsApp: {whatsapp_count}

Choose an action:
    """
    await query.edit_message_text(menu_text, reply_markup=owner_account_management(), parse_mode='Markdown')

# Admin management functions
async def manage_admins(query):
    menu_text = """
🛡️ *Admin Management*

Choose an action:
• *Add Admin* - Grant admin privileges to a user
• *Remove Admin* - Revoke admin privileges  
• *List Admins* - View all current admins

Only the owner can manage admins.
    """
    await query.edit_message_text(menu_text, parse_mode='Markdown', reply_markup=manage_admins_menu())

async def add_admin_handler(query, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_admin_add'] = True
    instruction_text = """
👥 *Add New Admin*

Please send the user ID of the person you want to make admin.

You can get user ID by:
1. Forwarding a message from the user to @userinfobot
2. Or ask the user to send /id in any chat

*Format:* Just send the numeric user ID

Type /cancel to cancel.
    """
    await query.edit_message_text(instruction_text, parse_mode='Markdown', reply_markup=back_to_main())
    return AWAITING_ADMIN_ID

async def handle_admin_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("❌ Only owner can add admins!")
        return
    
    if not context.user_data.get('awaiting_admin_add'):
        await update.message.reply_text("❌ No admin addition in progress!")
        return
    
    try:
        new_admin_id = int(update.message.text.strip())
        target_user = db.get_user(new_admin_id)
        if not target_user:
            db.create_user(new_admin_id, "Unknown")
        
        db.add_admin(new_admin_id)
        context.user_data['awaiting_admin_add'] = False
        
        success_text = f"""
✅ *Admin Added Successfully!*

🆔 User ID: `{new_admin_id}`
🛡️ Role: Admin

The user now has admin privileges in the bot.
        """
        await update.message.reply_text(success_text, parse_mode='Markdown', reply_markup=manage_admins_menu())
        
        # Notify new admin
        try:
            await context.bot.send_message(
                new_admin_id,
                "🎉 *You have been promoted to Admin!*\n\nYou now have access to admin features in the bot.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify new admin {new_admin_id}: {e}")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID! Please send a numeric user ID.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error adding admin: {str(e)}")

async def list_admins_handler(query):
    admins = db.get_all_admins()
    if not admins:
        await query.edit_message_text("📝 No admins found besides the owner.", reply_markup=manage_admins_menu())
        return
    
    admin_list_text = "🛡️ *Current Admins*\n\n"
    for admin in admins:
        user_id, username, is_admin_flag = admin
        status = "👑 Owner" if user_id == config.OWNER_ID else "🛡️ Admin"
        name = f"@{username}" if username else f"User {user_id}"
        admin_list_text += f"• {name}\n🆔 `{user_id}` | {status}\n\n"
    
    await query.edit_message_text(admin_list_text, parse_mode='Markdown', reply_markup=admin_list_menu(admins))

async def remove_admin_confirm(query):
    admin_id = int(query.data.split('_')[-1])
    if admin_id == config.OWNER_ID:
        await query.edit_message_text("❌ Cannot remove owner!", reply_markup=manage_admins_menu())
        return
    
    admin_user = db.get_user(admin_id)
    admin_name = f"@{admin_user[1]}" if admin_user and admin_user[1] else f"User {admin_id}"
    
    confirm_text = f"""
⚠️ *Confirm Admin Removal*

Are you sure you want to remove admin privileges from {admin_name}?

🆔 User ID: `{admin_id}`

This action cannot be undone!
    """
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Remove", callback_data=f"remove_admin_final_{admin_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="list_admins")]
    ]
    await query.edit_message_text(confirm_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def remove_admin_final(query, context: ContextTypes.DEFAULT_TYPE):
    admin_id = int(query.data.split('_')[-1])
    if admin_id == config.OWNER_ID:
        await query.edit_message_text("❌ Cannot remove owner!", reply_markup=manage_admins_menu())
        return
    
    admin_user = db.get_user(admin_id)
    admin_name = f"@{admin_user[1]}" if admin_user and admin_user[1] else f"User {admin_id}"
    db.remove_admin(admin_id)
    
    success_text = f"""
✅ *Admin Removed Successfully!*

👤 User: {admin_name}
🆔 ID: `{admin_id}`

Admin privileges have been revoked.
    """
    await query.edit_message_text(success_text, parse_mode='Markdown', reply_markup=manage_admins_menu())
    
    # Notify removed admin
    try:
        await context.bot.send_message(
            admin_id,
            "ℹ️ *Your admin privileges have been removed.*\n\nYou no longer have access to admin features.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to notify removed admin {admin_id}: {e}")

# Account management functions
async def add_accounts(query, context: ContextTypes.DEFAULT_TYPE):
    data = query.data
    account_type = "telegram" if "telegram" in data else "whatsapp"
    
    context.user_data['adding_accounts'] = True
    context.user_data['account_type'] = account_type
    
    instruction_text = f"""
📝 *Adding {account_type.title()} Accounts*

Please send accounts in the following format:
`phone_number:otp_code` or just `phone_number`

*Examples:*
`+1234567890:123456`
`+1234567891`
`+1234567892:654321`

You can send multiple accounts at once, each on a new line.

Type /cancel to stop adding accounts.
    """
    await query.edit_message_text(instruction_text, parse_mode='Markdown')
    return AWAITING_ACCOUNTS

async def handle_accounts_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("❌ Access denied!")
        return
    
    if not context.user_data.get('adding_accounts'):
        await update.message.reply_text("❌ No account addition in progress!")
        return
    
    account_type = context.user_data.get('account_type')
    text = update.message.text
    accounts_added = 0
    errors = []
    
    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        try:
            if ':' in line:
                phone_number, otp_code = line.split(':', 1)
                phone_number = phone_number.strip()
                otp_code = otp_code.strip()
            else:
                phone_number = line.strip()
                otp_code = None
            
            if not phone_number.startswith('+'):
                errors.append(f"Line {i}: Invalid phone number format")
                continue
            
            price = config.TELEGRAM_OTP_PRICE if account_type == "telegram" else config.WHATSAPP_OTP_PRICE
            db.add_account(account_type, phone_number, price, otp_code)
            accounts_added += 1
            
        except Exception as e:
            errors.append(f"Line {i}: {str(e)}")
    
    context.user_data['adding_accounts'] = False
    context.user_data['account_type'] = None
    
    result_text = f"""
✅ *Accounts Added Successfully*

📊 Summary:
• Type: {account_type.title()}
• Added: {accounts_added} accounts
• Errors: {len(errors)}
    """
    
    if errors:
        result_text += "\n\n❌ Errors:\n" + "\n".join(errors[:10])
    
    await update.message.reply_text(result_text, parse_mode='Markdown', reply_markup=owner_panel())
    return ConversationHandler.END

async def view_all_accounts(query):
    accounts_count = db.get_available_accounts_count()
    telegram_count = accounts_count.get('telegram', 0)
    whatsapp_count = accounts_count.get('whatsapp', 0)
    
    count_text = f"""
📊 *Account Statistics:*
• Telegram Available: {telegram_count}
• WhatsApp Available: {whatsapp_count}
    """
    
    await query.edit_message_text(count_text, parse_mode='Markdown', reply_markup=owner_account_management())

# User management
async def manage_users(query):
    menu_text = """
👥 *User Management*

Choose an action:
• *All Users* - View and manage all users
• *Blocked Users* - View and unblock users

Use the buttons below to manage users.
    """
    await query.edit_message_text(menu_text, parse_mode='Markdown', reply_markup=manage_users_menu())

async def list_all_users(query, context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_users()
    if not users:
        await query.edit_message_text("📝 No users found.", reply_markup=manage_users_menu())
        return
    
    users_text = "👥 *All Users*\n\n"
    for user in users[:10]:  # Show first 10 users
        user_id, username, balance, is_blocked, is_admin, joined_date = user
        status = "🚫" if is_blocked else "✅"
        admin_badge = " 🛡️" if is_admin else ""
        name = f"@{username}" if username else f"User {user_id}"
        
        users_text += f"{status} {name}{admin_badge}\n"
        users_text += f"   🆔 `{user_id}` | 💰 ₹{balance}\n\n"
    
    await query.edit_message_text(users_text, parse_mode='Markdown', reply_markup=manage_users_menu())

# Broadcast function
async def start_broadcast(query, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_broadcast'] = True
    instruction_text = """
📢 *Broadcast Message*

Please send the message you want to broadcast to all users.

You can include formatting using Markdown.

Type /cancel to cancel.
    """
    await query.edit_message_text(instruction_text, parse_mode='Markdown')
    return AWAITING_BROADCAST

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        await update.message.reply_text("❌ Only owner can broadcast!")
        return
    
    if not context.user_data.get('awaiting_broadcast'):
        await update.message.reply_text("❌ No broadcast in progress!")
        return
    
    broadcast_text = update.message.text
    users = db.get_all_users()
    success_count = 0
    fail_count = 0
    
    await update.message.reply_text("🔄 Starting broadcast...")
    
    for user in users:
        try:
            await context.bot.send_message(
                user[0],  # user_id
                f"📢 *Broadcast Message*\n\n{broadcast_text}",
                parse_mode='Markdown'
            )
            success_count += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            fail_count += 1
            logger.error(f"Failed to send broadcast to user {user[0]}: {e}")
    
    context.user_data['awaiting_broadcast'] = False
    
    result_text = f"""
✅ *Broadcast Completed*

📊 Results:
• ✅ Successful: {success_count}
• ❌ Failed: {fail_count}
• 📊 Total: {len(users)}
    """
    await update.message.reply_text(result_text, parse_mode='Markdown', reply_markup=owner_panel())
    return ConversationHandler.END

# Order history
async def view_user_orders(query, user_id):
    orders = db.get_user_orders(user_id)
    if not orders:
        await query.edit_message_text("📭 You haven't made any purchases yet!", reply_markup=back_to_main())
        return
    
    orders_text = "📋 *Your Order History*\n\n"
    for order in orders[:5]:  # Show last 5 orders
        order_id, _, acc_type, phone, status, price, purchased_at, completed_at, refund = order
        status_emoji = {'success': '✅', 'failed': '❌', 'cancelled': '🔄', 'pending': '⏳'}.get(status, '❓')
        orders_text += f"{status_emoji} *Order #{order_id}*\n"
        orders_text += f"📱 {acc_type.title()} | `{phone}`\n"
        orders_text += f"💰 ₹{price} | Status: {status}\n"
        orders_text += f"📅 {purchased_at}\n"
        if refund > 0:
            orders_text += f"🔄 Refund: ₹{refund}\n"
        orders_text += "\n"
    
    await query.edit_message_text(orders_text, parse_mode='Markdown', reply_markup=back_to_main())

# Payment approval system (placeholder implementations)
async def show_pending_payments(query):
    pending_text = """
⏳ *Pending Payments*

No pending payments at the moment.
    """
    await query.edit_message_text(pending_text, reply_markup=back_to_main(), parse_mode='Markdown')

async def handle_payment_approval(query, data, user_id):
    payment_id = data.split('_')[-1]
    if data.startswith("approve_payment_"):
        await query.edit_message_text("✅ Payment approved!", reply_markup=back_to_main())
    else:
        await query.edit_message_text("❌ Payment declined!", reply_markup=back_to_main())

# UTR handling
async def handle_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    utr = update.message.text
    
    if len(utr) < 10 or not utr.isdigit():
        await update.message.reply_text("❌ Invalid UTR format! Please send a valid UTR number.")
        return
    
    message = f"""
💰 *New Payment Request*

👤 User: {user_id} (@{update.effective_user.username})
🔢 UTR: `{utr}`
    """
    
    # Notify all admins
    admins = db.get_all_admins()
    for admin in admins:
        try:
            await context.bot.send_message(admin[0], message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to notify admin {admin[0]}: {e}")
    
    await update.message.reply_text(
        "✅ UTR received! Your payment is under review. You'll be notified once approved.",
        reply_markup=back_to_main()
    )

# Cancel handlers
async def cancel_adding_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['adding_accounts'] = False
    context.user_data['account_type'] = None
    await update.message.reply_text("❌ Account addition cancelled.", reply_markup=owner_panel())
    return ConversationHandler.END

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_broadcast'] = False
    await update.message.reply_text("❌ Broadcast cancelled.", reply_markup=owner_panel())
    return ConversationHandler.END

async def cancel_admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_admin_add'] = False
    await update.message.reply_text("❌ Admin addition cancelled.", reply_markup=manage_admins_menu())
    return ConversationHandler.END

def main():
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("mybalance", balance_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add conversation handlers
    # Account addition conversation
    account_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_accounts, pattern="^(add_telegram_accounts|add_whatsapp_accounts)$")],
        states={
            AWAITING_ACCOUNTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_accounts_input)]
        },
        fallbacks=[CommandHandler("cancel", cancel_adding_accounts)]
    )
    
    # Broadcast conversation
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast, pattern="^broadcast$")],
        states={
            AWAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message)]
        },
        fallbacks=[CommandHandler("cancel", cancel_broadcast)]
    )
    
    # Admin addition conversation
    admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_admin_handler, pattern="^add_admin$")],
        states={
            AWAITING_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_id_input)]
        },
        fallbacks=[CommandHandler("cancel", cancel_admin_add)]
    )
    
    application.add_handler(account_conv_handler)
    application.add_handler(broadcast_conv_handler)
    application.add_handler(admin_conv_handler)
    
    # Add UTR message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_utr))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == '__main__':
    main()