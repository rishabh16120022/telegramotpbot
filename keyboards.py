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
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
