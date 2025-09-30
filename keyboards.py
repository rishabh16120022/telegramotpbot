from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from database import db

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from database import db


# ========== OTP ACTIONS MENUS ==========
def otp_actions_menu(order_id):
    """Menu for OTP purchase actions"""
    keyboard = [
        [
            InlineKeyboardButton("👀 View OTP", callback_data=f"view_otp_{order_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_otp_{order_id}")
        ],
        [InlineKeyboardButton("🔄 Refresh Status", callback_data=f"refresh_otp_{order_id}")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def otp_received_menu(order_id):
    """Menu after OTP is received"""
    keyboard = [
        [InlineKeyboardButton("✅ Confirm OTP Received", callback_data=f"confirm_otp_{order_id}")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def otp_pending_menu(order_id):
    """Menu when OTP is still pending"""
    keyboard = [
        [InlineKeyboardButton("⏳ OTP Pending...", callback_data="none")],
        [
            InlineKeyboardButton("👀 View OTP", callback_data=f"view_otp_{order_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_otp_{order_id}")
        ],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== BUY MENUS ==========
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

# ... (rest of your existing keyboard functions remain the same) ...
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

# ========== ADMIN MANAGEMENT ==========
def manage_admins_menu():
    keyboard = [
        [InlineKeyboardButton("👥 Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("📋 List Admins", callback_data="list_admins")],
        [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_list_menu(admins):
    keyboard = []
    for admin in admins:
        user_id, username, is_admin = admin
        status = "👑 Owner" if user_id == config.OWNER_ID else "🛡️ Admin"
        name = f"@{username}" if username else f"User {user_id}"
        
        if user_id != config.OWNER_ID:  # Don't show remove button for owner
            keyboard.append([InlineKeyboardButton(f"{name} - {status}", callback_data=f"remove_admin_{user_id}")])
        else:
            keyboard.append([InlineKeyboardButton(f"{name} - {status}", callback_data="none")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="manage_admins")])
    return InlineKeyboardMarkup(keyboard)

# ========== ACCOUNT MANAGEMENT ==========
def owner_account_management():
    keyboard = [
        [InlineKeyboardButton("➕ Add Telegram Accounts", callback_data="add_telegram_accounts")],
        [InlineKeyboardButton("➕ Add WhatsApp Accounts", callback_data="add_whatsapp_accounts")],
        [InlineKeyboardButton("📋 View All Accounts", callback_data="view_all_accounts")],
        [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== USER MANAGEMENT ==========
def manage_users_menu():
    keyboard = [
        [InlineKeyboardButton("📋 All Users", callback_data="list_all_users")],
        [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def all_users_menu(users):
    keyboard = []
    for user in users[:15]:  # Show first 15 users
        user_id, username, balance, is_blocked, is_admin, joined_date = user
        name = f"@{username}" if username else f"User {user_id}"
        status = "🚫" if is_blocked else "✅"
        keyboard.append([InlineKeyboardButton(f"{status} {name} - ₹{balance}", callback_data=f"view_user_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="manage_users")])
    return InlineKeyboardMarkup(keyboard)

def user_actions_menu(user_id):
    keyboard = [
        [
            InlineKeyboardButton("➕ ₹100", callback_data=f"add_balance_{user_id}_100"),
            InlineKeyboardButton("➕ ₹500", callback_data=f"add_balance_{user_id}_500")
        ],
        [
            InlineKeyboardButton("➕ ₹1000", callback_data=f"add_balance_{user_id}_1000"),
            InlineKeyboardButton("➖ ₹100", callback_data=f"deduct_balance_{user_id}_100")
        ],
        [
            InlineKeyboardButton("🚫 Block", callback_data=f"block_user_{user_id}"),
            InlineKeyboardButton("✅ Unblock", callback_data=f"unblock_user_{user_id}")
        ],
        [InlineKeyboardButton("🔙 Back to Users", callback_data="list_all_users")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== PAYMENT APPROVAL SYSTEM ==========
def pending_payments_menu(payments):
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
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve Payment", callback_data=f"approve_payment_{payment_id}"),
            InlineKeyboardButton("❌ Decline Payment", callback_data=f"decline_payment_{payment_id}")
        ],
        [InlineKeyboardButton("🔙 Back to Payments", callback_data="pending_payments")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== OTP ACTIONS MENUS ==========
def otp_actions_menu(order_id):
    """Menu for OTP purchase actions"""
    keyboard = [
        [
            InlineKeyboardButton("👀 View OTP", callback_data=f"view_otp_{order_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_otp_{order_id}")
        ],
        [InlineKeyboardButton("🔄 Refresh Status", callback_data=f"refresh_otp_{order_id}")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def otp_received_menu(order_id):
    """Menu after OTP is received"""
    keyboard = [
        [InlineKeyboardButton("✅ Confirm OTP Received", callback_data=f"confirm_otp_{order_id}")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def otp_pending_menu(order_id):
    """Menu when OTP is still pending"""
    keyboard = [
        [InlineKeyboardButton("⏳ OTP Pending...", callback_data="none")],
        [
            InlineKeyboardButton("👀 View OTP", callback_data=f"view_otp_{order_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_otp_{order_id}")
        ],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

