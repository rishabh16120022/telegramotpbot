from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from database import db

# ========== MAIN MENUS ==========
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📱 Buy OTP", callback_data="buy_otp")],
        [InlineKeyboardButton("💳 Buy Session", callback_data="buy_session")],
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("📋 My Orders", callback_data="my_orders")],
        [InlineKeyboardButton("👑 Owner Panel", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]])

def buy_otp_menu():
    keyboard = [
        [InlineKeyboardButton("📲 Telegram OTP", callback_data="buy_telegram_otp")],
        [InlineKeyboardButton("💚 WhatsApp OTP", callback_data="buy_whatsapp_otp")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def buy_session_menu():
    keyboard = [
        [InlineKeyboardButton("📲 Telegram Session", callback_data="buy_telegram_session")],
        [InlineKeyboardButton("💚 WhatsApp Session", callback_data="buy_whatsapp_session")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def deposit_menu():
    keyboard = [
        [InlineKeyboardButton("📱 Pay via QR", callback_data="show_qr")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== PAYMENT APPROVAL SYSTEM ==========
def pending_payments_menu(payments):
    """Keyboard for pending payments list"""
    keyboard = []
    
    for payment in payments[:10]:
        payment_id, user_id, amount, utr, status, admin_id, created_at, username = payment
        display_text = f"💰 ₹{amount} - User {user_id}"
        if username:
            display_text = f"💰 ₹{amount} - @{username}"
            
        keyboard.append([InlineKeyboardButton(display_text, callback_data=f"view_payment_{payment_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="owner_panel")])
    return InlineKeyboardMarkup(keyboard)

def payment_actions_menu(payment_id):
    """Keyboard for payment approval/decline"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve Payment", callback_data=f"approve_payment_{payment_id}"),
            InlineKeyboardButton("❌ Decline Payment", callback_data=f"decline_payment_{payment_id}")
        ],
        [InlineKeyboardButton("🔙 Back to Payments", callback_data="pending_payments")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== OWNER & ADMIN PANELS ==========
def owner_panel():
    keyboard = [
        [InlineKeyboardButton("⏳ Pending Payments", callback_data="pending_payments")],
        [InlineKeyboardButton("👥 Manage Users", callback_data="manage_users")],
        [InlineKeyboardButton("🛡️ Manage Admins", callback_data="manage_admins")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("📱 Manage Accounts", callback_data="owner_account_management")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
