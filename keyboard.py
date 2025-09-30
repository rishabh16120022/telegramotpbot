from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

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

def owner_panel():
    keyboard = [
        [InlineKeyboardButton("👥 Manage Users", callback_data="manage_users")],
        [InlineKeyboardButton("🛡️ Manage Admins", callback_data="manage_admins")],
        [InlineKeyboardButton("📊 All Stats", callback_data="all_stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("⏳ Pending Payments", callback_data="pending_payments")],
        [InlineKeyboardButton("📱 Manage Accounts", callback_data="owner_account_management")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def owner_account_management():
    keyboard = [
        [InlineKeyboardButton("➕ Add Telegram Accounts", callback_data="add_telegram_accounts")],
        [InlineKeyboardButton("➕ Add WhatsApp Accounts", callback_data="add_whatsapp_accounts")],
        [InlineKeyboardButton("📋 View All Accounts", callback_data="view_all_accounts")],
        [InlineKeyboardButton("🔙 Back to Owner Panel", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def manage_admins_menu():
    keyboard = [
        [InlineKeyboardButton("👥 Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("🗑️ Remove Admin", callback_data="remove_admin")],
        [InlineKeyboardButton("📋 List Admins", callback_data="list_admins")],
        [InlineKeyboardButton("🔙 Back to Owner Panel", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def manage_users_menu():
    keyboard = [
        [InlineKeyboardButton("📋 All Users", callback_data="list_all_users")],
        [InlineKeyboardButton("🔙 Back to Owner Panel", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_list_menu(admins):
    keyboard = []
    for admin in admins:
        user_id, username, is_admin = admin
        display_name = f"@{username}" if username else f"User {user_id}"
        keyboard.append([InlineKeyboardButton(f"👤 {display_name}", callback_data=f"view_admin_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="manage_admins")])
    return InlineKeyboardMarkup(keyboard)

def admin_actions_menu(admin_id, is_owner=False):
    keyboard = []
    if not is_owner:
        keyboard.append([InlineKeyboardButton("🗑️ Remove Admin", callback_data=f"remove_admin_confirm_{admin_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Admins", callback_data="list_admins")])
    return InlineKeyboardMarkup(keyboard)

def user_actions_menu(user_id):
    keyboard = [
        [InlineKeyboardButton("➕ Add Balance", callback_data=f"admin_add_balance_{user_id}")],
        [InlineKeyboardButton("➖ Deduct Balance", callback_data=f"admin_deduct_balance_{user_id}")],
        [InlineKeyboardButton("🛡️ Make Admin", callback_data=f"admin_make_admin_{user_id}")],
        [InlineKeyboardButton("🚫 Block User", callback_data=f"admin_block_user_{user_id}")],
        [InlineKeyboardButton("✅ Unblock User", callback_data=f"admin_unblock_user_{user_id}")],
        [InlineKeyboardButton("🔙 Back to Users", callback_data="list_all_users")]
    ]
    return InlineKeyboardMarkup(keyboard)

def payment_approval(payment_id):
    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{payment_id}")],
        [InlineKeyboardButton("❌ Decline", callback_data=f"decline_payment_{payment_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="pending_payments")]
    ]
    return InlineKeyboardMarkup(keyboard)
