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
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])

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
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("📱 Manage Accounts", callback_data="owner_account_management")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def owner_account_management():
    keyboard = [
        [InlineKeyboardButton("➕ Add Telegram", callback_data="add_telegram_accounts")],
        [InlineKeyboardButton("➕ Add WhatsApp", callback_data="add_whatsapp_accounts")],
        [InlineKeyboardButton("📋 View Accounts", callback_data="view_all_accounts")],
        [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def manage_admins_menu():
    keyboard = [
        [InlineKeyboardButton("👥 Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("🗑️ Remove Admin", callback_data="remove_admin")],
        [InlineKeyboardButton("📋 List Admins", callback_data="list_admins")],
        [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def manage_users_menu():
    keyboard = [
        [InlineKeyboardButton("📋 All Users", callback_data="list_all_users")],
        [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_list_menu(admins):
    keyboard = []
    for admin in admins:
        keyboard.append([InlineKeyboardButton(f"👤 {admin[1] or f'User {admin[0]}'}", callback_data=f"view_admin_{admin[0]}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="manage_admins")])
    return InlineKeyboardMarkup(keyboard)
