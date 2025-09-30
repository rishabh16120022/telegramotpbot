from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ... (keep all existing keyboard functions) ...

def pending_payments_menu(payments):
    """Keyboard for pending payments list"""
    keyboard = []
    for payment in payments:
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
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_payment_{payment_id}"),
            InlineKeyboardButton("❌ Decline", callback_data=f"decline_payment_{payment_id}")
        ],
        [InlineKeyboardButton("🔙 Back to Payments", callback_data="pending_payments")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_panel():
    """Admin panel with payment approval access"""
    keyboard = [
        [InlineKeyboardButton("⏳ Pending Payments", callback_data="pending_payments")],
        [InlineKeyboardButton("👥 Manage Users", callback_data="manage_users")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def user_actions_menu(user_id):
    """Keyboard for user management with balance options"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Add ₹100", callback_data=f"add_balance_{user_id}_100"),
            InlineKeyboardButton("➕ Add ₹500", callback_data=f"add_balance_{user_id}_500")
        ],
        [
            InlineKeyboardButton("➕ Add ₹1000", callback_data=f"add_balance_{user_id}_1000"),
            InlineKeyboardButton("➖ Deduct ₹100", callback_data=f"deduct_balance_{user_id}_100")
        ],
        [InlineKeyboardButton("🛡️ Make Admin", callback_data=f"make_admin_{user_id}")],
        [InlineKeyboardButton("🚫 Block User", callback_data=f"block_user_{user_id}")],
        [InlineKeyboardButton("✅ Unblock User", callback_data=f"unblock_user_{user_id}")],
        [InlineKeyboardButton("🔙 Back to Users", callback_data="list_all_users")]
    ]
    return InlineKeyboardMarkup(keyboard)
