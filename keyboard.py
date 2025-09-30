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
