from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
import config
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
    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]]
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

def admin_panel():
    keyboard = [
        [InlineKeyboardButton("⏳ Pending Payments", callback_data="pending_payments")],
        [InlineKeyboardButton("👥 Manage Users", callback_data="manage_users")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== PAYMENT APPROVAL SYSTEM ==========

def pending_payments_menu(payments):
    """Keyboard for pending payments list"""
    keyboard = []
    
    for payment in payments[:10]:  # Show first 10 payments
        payment_id, user_id, amount, utr, status, admin_id, created_at, username = payment
        display_text = f"💰 ₹{amount} - User {user_id}"
        if username:
            display_text = f"💰 ₹{amount} - @{username}"
        
        # Truncate long text
        if len(display_text) > 30:
            display_text = display_text[:27] + "..."
            
        keyboard.append([InlineKeyboardButton(display_text, callback_data=f"view_payment_{payment_id}")])
    
    # Add payment stats if available
    payment_stats = db.get_payment_stats()
    if payment_stats['pending_count'] > 0:
        stats_text = f"⏳ {payment_stats['pending_count']} Pending"
        keyboard.append([InlineKeyboardButton(stats_text, callback_data="pending_payments")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Owner Panel", callback_data="owner_panel")])
    return InlineKeyboardMarkup(keyboard)

def payment_actions_menu(payment_id):
    """Keyboard for payment approval/decline with quick actions"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve Payment", callback_data=f"approve_payment_{payment_id}"),
            InlineKeyboardButton("❌ Decline Payment", callback_data=f"decline_payment_{payment_id}")
        ],
        [InlineKeyboardButton("🔙 Back to Payments", callback_data="pending_payments")]
    ]
    return InlineKeyboardMarkup(keyboard)

def payment_review_menu(payment_id):
    """Alternative simpler payment review menu"""
    keyboard = [
        [InlineKeyboardButton("✅ Approve & Add Balance", callback_data=f"approve_payment_{payment_id}")],
        [InlineKeyboardButton("❌ Decline Payment", callback_data=f"decline_payment_{payment_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="pending_payments")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ACCOUNT MANAGEMENT ==========

def owner_account_management():
    keyboard = [
        [InlineKeyboardButton("➕ Add Telegram Accounts", callback_data="add_telegram_accounts")],
        [InlineKeyboardButton("➕ Add WhatsApp Accounts", callback_data="add_whatsapp_accounts")],
        [InlineKeyboardButton("📋 View All Accounts", callback_data="view_all_accounts")],
        [InlineKeyboardButton("🔙 Back to Owner Panel", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ADMIN MANAGEMENT ==========

def manage_admins_menu():
    keyboard = [
        [InlineKeyboardButton("👥 Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("🗑️ Remove Admin", callback_data="remove_admin")],
        [InlineKeyboardButton("📋 List Admins", callback_data="list_admins")],
        [InlineKeyboardButton("🔙 Back to Owner Panel", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_list_menu(admins):
    keyboard = []
    for admin in admins:
        user_id, username, is_admin = admin
        display_name = f"@{username}" if username else f"User {user_id}"
        status = "👑 Owner" if user_id == config.OWNER_ID else "🛡️ Admin"
        
        button_text = f"{display_name} ({status})"
        if len(button_text) > 30:
            button_text = button_text[:27] + "..."
            
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_admin_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="manage_admins")])
    return InlineKeyboardMarkup(keyboard)

def admin_actions_menu(admin_id, is_owner=False):
    keyboard = []
    if not is_owner:
        keyboard.append([InlineKeyboardButton("🗑️ Remove Admin", callback_data=f"remove_admin_confirm_{admin_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Back to Admins", callback_data="list_admins")])
    return InlineKeyboardMarkup(keyboard)

# ========== USER MANAGEMENT ==========

def manage_users_menu():
    keyboard = [
        [InlineKeyboardButton("📋 All Users", callback_data="list_all_users")],
        [InlineKeyboardButton("🔙 Back to Owner Panel", callback_data="owner_panel")]
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
        [
            InlineKeyboardButton("🛡️ Make Admin", callback_data=f"make_admin_{user_id}"),
            InlineKeyboardButton("🚫 Block User", callback_data=f"block_user_{user_id}")
        ],
        [InlineKeyboardButton("✅ Unblock User", callback_data=f"unblock_user_{user_id}")],
        [InlineKeyboardButton("🔙 Back to Users", callback_data="list_all_users")]
    ]
    return InlineKeyboardMarkup(keyboard)

def quick_balance_menu(user_id):
    """Simplified balance management menu"""
    keyboard = [
        [
            InlineKeyboardButton("➕ ₹100", callback_data=f"add_balance_{user_id}_100"),
            InlineKeyboardButton("➕ ₹500", callback_data=f"add_balance_{user_id}_500"),
            InlineKeyboardButton("➕ ₹1000", callback_data=f"add_balance_{user_id}_1000")
        ],
        [
            InlineKeyboardButton("➖ ₹100", callback_data=f"deduct_balance_{user_id}_100"),
            InlineKeyboardButton("➖ ₹500", callback_data=f"deduct_balance_{user_id}_500")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="list_all_users")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ORDER MANAGEMENT ==========

def order_actions_menu(order_id):
    """Keyboard for order management"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Mark Complete", callback_data=f"complete_order_{order_id}"),
            InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{order_id}")
        ],
        [InlineKeyboardButton("🔄 Refund", callback_data=f"refund_order_{order_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="my_orders")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== BROADCAST & SETTINGS ==========

def broadcast_confirmation():
    """Keyboard for broadcast confirmation"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Send Broadcast", callback_data="confirm_broadcast"),
            InlineKeyboardButton("❌ Cancel", callback_data="owner_panel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def settings_menu():
    """Keyboard for bot settings"""
    keyboard = [
        [InlineKeyboardButton("💰 Update Prices", callback_data="update_prices")],
        [InlineKeyboardButton("📊 View Statistics", callback_data="view_stats")],
        [InlineKeyboardButton("🔧 Maintenance", callback_data="maintenance")],
        [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== PAYMENT HISTORY ==========

def payment_history_menu(user_id):
    """Keyboard for user payment history"""
    keyboard = [
        [InlineKeyboardButton("📋 My Payments", callback_data=f"my_payments_{user_id}")],
        [InlineKeyboardButton("💳 Add Funds", callback_data="deposit")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== QUICK ACTIONS ==========

def quick_actions_menu():
    """Quick actions for admins"""
    keyboard = [
        [
            InlineKeyboardButton("⏳ Payments", callback_data="pending_payments"),
            InlineKeyboardButton("👥 Users", callback_data="list_all_users")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="view_stats"),
            InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")
        ],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== CONFIRMATION DIALOGS ==========

def confirmation_menu(action, target_id):
    """Generic confirmation menu"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}_{target_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{action}_{target_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def yes_no_menu(action, target_id):
    """Yes/No confirmation menu"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"yes_{action}_{target_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"no_{action}_{target_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Import db for payment stats (add this at the top if needed)
from database import db
import config
