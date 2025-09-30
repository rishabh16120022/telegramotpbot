import logging
import sqlite3
import asyncio
import random
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    await update.message.reply_text(welcome_message, reply_markup=main_menu(), parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
📊 Stats - View statistics
📋 My Orders - Order history

*Minimum Deposit:* ₹50
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        stats_text = f"""
📊 *Your Statistics*

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

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        await update.message.reply_text(f"💳 *Your Balance:* ₹{user[2]}", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ User not found!")

# ========== BUTTON HANDLER ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    try:
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
        elif data == "show_qr":
            await show_qr_code(query)
        elif data == "owner_panel":
            if is_owner(user_id):
                await show_owner_panel(query)
        elif data == "manage_admins":
            if is_owner(user_id):
                await manage_admins(query)
        elif data == "add_admin":
            if is_owner(user_id):
                await add_admin_handler(query, context)
        elif data == "list_admins":
            if is_owner(user_id):
                await list_admins_handler(query)
        elif data == "owner_account_management":
            if is_owner(user_id):
                await show_account_management(query)
        elif data in ["add_telegram_accounts", "add_whatsapp_accounts"]:
            if is_owner(user_id):
                await add_accounts(query, context)
        elif data == "view_all_accounts":
            if is_owner(user_id):
                await view_all_accounts(query)
        elif data.startswith("buy_"):
            await handle_purchase(query, data, user_id, context)
        elif data.startswith("cancel_order_"):
            await cancel_order(query, context)
        elif data.startswith("remove_admin_confirm_"):
            if is_owner(user_id):
                await remove_admin_confirm(query)
        elif data.startswith("remove_admin_final_"):
            if is_owner(user_id):
                await remove_admin_final(query, context)
        elif data == "manage_users":
            if is_admin(user_id):
                await manage_users(query)
        elif data == "list_all_users":
            if is_admin(user_id):
                await list_all_users(query, context)
        elif data == "broadcast":
            if is_owner(user_id):
                await start_broadcast(query, context)
                
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.edit_message_text("❌ An error occurred. Please try again.")

# ========== MENU FUNCTIONS ==========
async def show_main_menu(query):
    accounts_count = db.get_available_accounts_count()
    telegram_count = accounts_count.get('telegram', 0)
    whatsapp_count = accounts_count.get('whatsapp', 0)
    
    menu_text = f"""
🏠 *Main Menu*

📊 *Available Accounts:*
📲 Telegram: {telegram_count}
💚 WhatsApp: {whatsapp_count}
    """
    await query.edit_message_text(menu_text, reply_markup=main_menu(), parse_mode='Markdown')

async def show_otp_menu(query):
    menu_text = """
📱 *Buy OTP*

• Telegram OTP - ₹10
• WhatsApp OTP - ₹15
    """
    await query.edit_message_text(menu_text, reply_markup=buy_otp_menu(), parse_mode='Markdown')

async def show_session_menu(query):
    menu_text = """
💳 *Buy Session*

• Telegram Session - ₹25
• WhatsApp Session - ₹25
    """
    await query.edit_message_text(menu_text, reply_markup=buy_session_menu(), parse_mode='Markdown')

async def show_deposit_menu(query):
    menu_text = f"""
💰 *Deposit Funds*

💳 *Minimum Deposit:* ₹{config.MIN_DEPOSIT}

Click below to see QR code for payment.
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
        """
        await query.edit_message_text(stats_text, reply_markup=back_to_main(), parse_mode='Markdown')

async def show_qr_code(query):
    qr_text = f"""
📱 *Payment QR Code*

💰 *Minimum Amount:* ₹{config.MIN_DEPOSIT}

{config.OWNER_QR_CODE}

*After payment:*
1. Send UTR number to admin
2. Wait for approval
    """
    await query.edit_message_text(qr_text, reply_markup=back_to_main(), parse_mode='Markdown')

# ========== PURCHASE SYSTEM ==========
async def handle_purchase(query, data, user_id, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(user_id)
    
    if user and user[5]:
        await query.edit_message_text("❌ Your account is blocked!", reply_markup=back_to_main())
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
        await query.edit_message_text(f"❌ Insufficient balance! Need ₹{price}", reply_markup=back_to_main())
        return
    
    account = db.get_available_account(account_type.replace('_session', ''))
    if not account:
        await query.edit_message_text("❌ No accounts available!", reply_markup=back_to_main())
        return
    
    order_id = db.create_order(user_id, account_type, account[2], None, price)
    db.update_balance(user_id, -price)
    
    progress_text = f"""
🔄 *Purchase In Progress...*

📞 Number: `{account[2]}`
💰 Amount: ₹{price}

⏳ Processing...
    """
    
    keyboard = [[InlineKeyboardButton("❌ Cancel & Refund", callback_data=f"cancel_order_{order_id}")]]
    await query.edit_message_text(progress_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    asyncio.create_task(process_otp_delivery(context, order_id, account[0], user_id))

async def process_otp_delivery(context: ContextTypes.DEFAULT_TYPE, order_id: int, account_id: int, user_id: int):
    await asyncio.sleep(random.randint(5, 15))
    
    order = db.get_order(order_id)
    if order and order[5] == 'pending':
        if random.random() < 0.9:
            otp_code = str(random.randint(100000, 999999))
            db.complete_order(order_id, 'success', otp_code)
            db.mark_account_sold(account_id, user_id)
            
            success_text = f"""
✅ *Order Completed!*

📞 Number: `{order[4]}`
🔑 OTP: `{otp_code}`
💰 Paid: ₹{order[6]}
            """
            try:
                await context.bot.send_message(user_id, success_text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
        else:
            db.complete_order(order_id, 'failed')
            db.update_balance(user_id, order[6])
            db.update_user_refund(user_id, order[6])
            
            fail_text = f"""
❌ *OTP Delivery Failed*

Refund issued: ₹{order[6]}
            """
            try:
                await context.bot.send_message(user_id, fail_text, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to send message: {e}")

async def cancel_order(query, context: ContextTypes.DEFAULT_TYPE):
    order_id = int(query.data.split('_')[-1])
    order = db.get_order(order_id)
    
    if not order or order[1] != query.from_user.id or order[5] != 'pending':
        await query.edit_message_text("❌ Cannot cancel order!", reply_markup=back_to_main())
        return
    
    db.complete_order(order_id, 'cancelled')
    db.update_balance(order[1], order[6])
    db.update_user_refund(order[1], order[6])
    
    await query.edit_message_text("✅ Order cancelled & refunded!", reply_markup=back_to_main())

# ========== OWNER/ADMIN FUNCTIONS ==========
async def show_owner_panel(query):
    await query.edit_message_text("👑 *Owner Panel*", reply_markup=owner_panel(), parse_mode='Markdown')

async def show_account_management(query):
    accounts_count = db.get_available_accounts_count()
    menu_text = f"""
📱 *Account Management*

📲 Telegram: {accounts_count.get('telegram', 0)}
💚 WhatsApp: {accounts_count.get('whatsapp', 0)}
    """
    await query.edit_message_text(menu_text, reply_markup=owner_account_management(), parse_mode='Markdown')

async def manage_admins(query):
    await query.edit_message_text("🛡️ *Admin Management*", reply_markup=manage_admins_menu(), parse_mode='Markdown')

async def add_admin_handler(query, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_admin_add'] = True
    await query.edit_message_text("👥 Send user ID to make admin:", parse_mode='Markdown')
    return AWAITING_ADMIN_ID

async def handle_admin_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Access denied!")
        return
    
    try:
        new_admin_id = int(update.message.text.strip())
        db.add_admin(new_admin_id)
        context.user_data['awaiting_admin_add'] = False
        await update.message.reply_text(f"✅ Admin added: {new_admin_id}", reply_markup=manage_admins_menu())
        
        try:
            await context.bot.send_message(new_admin_id, "🎉 You are now an admin!")
        except:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")

async def list_admins_handler(query):
    admins = db.get_all_admins()
    admin_list = "🛡️ *Admins:*\n\n"
    for admin in admins:
        admin_list += f"• {admin[1] or f'User {admin[0]}'} (`{admin[0]}`)\n"
    await query.edit_message_text(admin_list, parse_mode='Markdown', reply_markup=admin_list_menu(admins))

async def remove_admin_confirm(query):
    admin_id = int(query.data.split('_')[-1])
    if admin_id == config.OWNER_ID:
        await query.edit_message_text("❌ Cannot remove owner!")
        return
    
    admin_user = db.get_user(admin_id)
    admin_name = admin_user[1] if admin_user and admin_user[1] else f"User {admin_id}"
    
    keyboard = [
        [InlineKeyboardButton("✅ Remove", callback_data=f"remove_admin_final_{admin_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="list_admins")]
    ]
    await query.edit_message_text(f"Remove admin {admin_name}?", reply_markup=InlineKeyboardMarkup(keyboard))

async def remove_admin_final(query, context: ContextTypes.DEFAULT_TYPE):
    admin_id = int(query.data.split('_')[-1])
    db.remove_admin(admin_id)
    await query.edit_message_text("✅ Admin removed!", reply_markup=manage_admins_menu())
    
    try:
        await context.bot.send_message(admin_id, "ℹ️ Your admin privileges were removed.")
    except:
        pass

async def add_accounts(query, context: ContextTypes.DEFAULT_TYPE):
    account_type = "telegram" if "telegram" in query.data else "whatsapp"
    context.user_data['adding_accounts'] = True
    context.user_data['account_type'] = account_type
    
    await query.edit_message_text(f"📝 Send {account_type} accounts:\n`phone:otp` or `phone`", parse_mode='Markdown')
    return AWAITING_ACCOUNTS

async def handle_accounts_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Access denied!")
        return
    
    account_type = context.user_data.get('account_type')
    text = update.message.text
    accounts_added = 0
    
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
            
        try:
            if ':' in line:
                phone, otp = line.split(':', 1)
            else:
                phone, otp = line.strip(), None
            
            if phone.startswith('+'):
                price = config.TELEGRAM_OTP_PRICE if account_type == "telegram" else config.WHATSAPP_OTP_PRICE
                db.add_account(account_type, phone, price, otp)
                accounts_added += 1
        except:
            pass
    
    context.user_data['adding_accounts'] = False
    await update.message.reply_text(f"✅ Added {accounts_added} accounts!", reply_markup=owner_panel())
    return ConversationHandler.END

async def view_all_accounts(query):
    accounts_count = db.get_available_accounts_count()
    await query.edit_message_text(
        f"📊 Accounts: Telegram({accounts_count.get('telegram', 0)}), WhatsApp({accounts_count.get('whatsapp', 0)})",
        reply_markup=owner_account_management()
    )

async def manage_users(query):
    await query.edit_message_text("👥 *User Management*", reply_markup=manage_users_menu(), parse_mode='Markdown')

async def list_all_users(query, context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_users()
    users_text = "👥 *Users:*\n\n"
    for user in users[:10]:
        users_text += f"• {user[1] or f'User {user[0]}'} - ₹{user[2]}\n"
    await query.edit_message_text(users_text, parse_mode='Markdown', reply_markup=manage_users_menu())

async def start_broadcast(query, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_broadcast'] = True
    await query.edit_message_text("📢 Send broadcast message:")
    return AWAITING_BROADCAST

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Access denied!")
        return
    
    broadcast_text = update.message.text
    users = db.get_all_users()
    success = 0
    
    for user in users:
        try:
            await context.bot.send_message(user[0], f"📢 {broadcast_text}")
            success += 1
            await asyncio.sleep(0.1)
        except:
            pass
    
    context.user_data['awaiting_broadcast'] = False
    await update.message.reply_text(f"✅ Sent to {success}/{len(users)} users", reply_markup=owner_panel())
    return ConversationHandler.END

async def view_user_orders(query, user_id):
    orders = db.get_user_orders(user_id)
    if not orders:
        await query.edit_message_text("📭 No orders yet!", reply_markup=back_to_main())
        return
    
    orders_text = "📋 *Your Orders:*\n\n"
    for order in orders[:5]:
        status_emoji = {'success': '✅', 'failed': '❌', 'cancelled': '🔄', 'pending': '⏳'}.get(order[5], '❓')
        orders_text += f"{status_emoji} {order[3]} - ₹{order[6]} - {order[5]}\n"
    
    await query.edit_message_text(orders_text, parse_mode='Markdown', reply_markup=back_to_main())

# ========== UTR HANDLING ==========
async def handle_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utr = update.message.text
    
    if len(utr) < 10 or not utr.isdigit():
        await update.message.reply_text("❌ Invalid UTR!")
        return
    
    message = f"💰 Payment Request\nUser: {update.effective_user.id}\nUTR: {utr}"
    
    admins = db.get_all_admins()
    for admin in admins:
        try:
            await context.bot.send_message(admin[0], message)
        except:
            pass
    
    await update.message.reply_text("✅ UTR received! Under review.", reply_markup=back_to_main())

# ========== CANCEL HANDLERS ==========
async def cancel_adding_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['adding_accounts'] = False
    await update.message.reply_text("❌ Cancelled.", reply_markup=owner_panel())
    return ConversationHandler.END

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_broadcast'] = False
    await update.message.reply_text("❌ Cancelled.", reply_markup=owner_panel())
    return ConversationHandler.END

async def cancel_admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_admin_add'] = False
    await update.message.reply_text("❌ Cancelled.", reply_markup=manage_admins_menu())
    return ConversationHandler.END

# ========== MAIN FUNCTION ==========
def main():
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("mybalance", balance_command))
    
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Conversation handlers
    account_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_accounts, pattern="^(add_telegram_accounts|add_whatsapp_accounts)$")],
        states={AWAITING_ACCOUNTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_accounts_input)]},
        fallbacks=[CommandHandler("cancel", cancel_adding_accounts)]
    )
    
    broadcast_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast, pattern="^broadcast$")],
        states={AWAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message)]},
        fallbacks=[CommandHandler("cancel", cancel_broadcast)]
    )
    
    admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_admin_handler, pattern="^add_admin$")],
        states={AWAITING_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_id_input)]},
        fallbacks=[CommandHandler("cancel", cancel_admin_add)]
    )
    
    application.add_handler(account_conv_handler)
    application.add_handler(broadcast_conv_handler)
    application.add_handler(admin_conv_handler)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_utr))
    
    logger.info("Starting Telegram Bot...")
    print("🤖 Bot starting on Render.com...")
    application.run_polling()

if __name__ == '__main__':
    main()
