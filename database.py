import sqlite3
import datetime
from typing import List, Tuple, Optional
import config

class Database:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path

    def get_user(self, user_id: int) -> Optional[Tuple]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    def create_user(self, user_id: int, username: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
        conn.close()

    def update_balance(self, user_id: int, amount: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        conn.close()

    def get_available_accounts_count(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT type, COUNT(*) FROM accounts WHERE status = "available" GROUP BY type')
        result = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in result}

    def add_account(self, account_type: str, phone_number: str, price: float, otp_code: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO accounts (type, phone_number, otp_code, price) VALUES (?, ?, ?, ?)', 
                      (account_type, phone_number, otp_code, price))
        conn.commit()
        conn.close()

    def get_available_account(self, account_type: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE type = ? AND status = "available" LIMIT 1', (account_type,))
        account = cursor.fetchone()
        
        if account:
            cursor.execute('UPDATE accounts SET status = "pending" WHERE id = ?', (account[0],))
            conn.commit()
        
        conn.close()
        return account

    def mark_account_sold(self, account_id: int, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE accounts SET status = "sold" WHERE id = ?', (account_id,))
        cursor.execute('UPDATE users SET accounts_bought = accounts_bought + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def create_order(self, user_id: int, account_type: str, phone_number: str, otp_code: str, price: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO account_orders (user_id, account_type, phone_number, otp_code, price) VALUES (?, ?, ?, ?, ?)', 
                      (user_id, account_type, phone_number, otp_code, price))
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id

    def get_order(self, order_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM account_orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        conn.close()
        return order

    def complete_order(self, order_id: int, status: str, otp_code: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == 'success' and otp_code:
            cursor.execute('UPDATE account_orders SET status = ?, otp_code = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?', 
                          (status, otp_code, order_id))
        elif status in ['failed', 'cancelled']:
            cursor.execute('SELECT price FROM account_orders WHERE id = ?', (order_id,))
            price = cursor.fetchone()[0]
            cursor.execute('UPDATE account_orders SET status = ?, completed_at = CURRENT_TIMESTAMP, refund_amount = ? WHERE id = ?', 
                          (status, price, order_id))
        else:
            cursor.execute('UPDATE account_orders SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?', 
                          (status, order_id))
        
        conn.commit()
        conn.close()

    def get_user_orders(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM account_orders WHERE user_id = ? ORDER BY purchased_at DESC', (user_id,))
        orders = cursor.fetchall()
        conn.close()
        return orders

    def update_user_refund(self, user_id: int, amount: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET total_refund = total_refund + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
        conn.close()

    def add_admin(self, user_id: int, username: str = None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        cursor.execute('UPDATE users SET is_admin = TRUE WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def remove_admin(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_admin = FALSE WHERE user_id = ? AND user_id != ?', (user_id, config.OWNER_ID))
        conn.commit()
        conn.close()

    def get_all_admins(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, is_admin FROM users WHERE is_admin = TRUE OR user_id = ?', (config.OWNER_ID,))
        admins = cursor.fetchall()
        conn.close()
        return admins

    def get_all_users(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, balance, is_blocked, is_admin, joined_date FROM users ORDER BY joined_date DESC')
        users = cursor.fetchall()
        conn.close()
        return users

    def block_user(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = TRUE WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def unblock_user(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = FALSE WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    # ========== PAYMENT MANAGEMENT METHODS ==========

    def create_payment_request(self, user_id: int, amount: float, utr: str):
        """Create a new payment request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payments (user_id, amount, utr, status) 
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, amount, utr))
        payment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return payment_id

    def get_pending_payments(self):
        """Get all pending payment requests"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.username 
            FROM payments p 
            LEFT JOIN users u ON p.user_id = u.user_id 
            WHERE p.status = 'pending' 
            ORDER BY p.created_at DESC
        ''')
        payments = cursor.fetchall()
        conn.close()
        return payments

    def get_payment(self, payment_id: int):
        """Get specific payment by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, u.username 
            FROM payments p 
            LEFT JOIN users u ON p.user_id = u.user_id 
            WHERE p.id = ?
        ''', (payment_id,))
        payment = cursor.fetchone()
        conn.close()
        return payment

    def approve_payment(self, payment_id: int, admin_id: int):
        """Approve payment and add balance to user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get payment details
        cursor.execute('SELECT user_id, amount FROM payments WHERE id = ?', (payment_id,))
        payment = cursor.fetchone()
        
        if payment:
            user_id, amount = payment
            # Update payment status
            cursor.execute('''
                UPDATE payments 
                SET status = 'approved', admin_id = ? 
                WHERE id = ?
            ''', (admin_id, payment_id))
            
            # Add balance to user
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            
            conn.commit()
            conn.close()
            return (user_id, amount)
        
        conn.close()
        return None

    def decline_payment(self, payment_id: int, admin_id: int):
        """Decline payment request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE payments 
            SET status = 'declined', admin_id = ? 
            WHERE id = ?
        ''', (admin_id, payment_id))
        conn.commit()
        conn.close()

    def get_user_payments(self, user_id: int):
        """Get payment history for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM payments 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        payments = cursor.fetchall()
        conn.close()
        return payments

    def get_payment_stats(self):
        """Get payment statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total pending payments
        cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "pending"')
        pending_count = cursor.fetchone()[0]
        
        # Total approved amount
        cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = "approved"')
        approved_total = cursor.fetchone()[0]
        
        # Total declined count
        cursor.execute('SELECT COUNT(*) FROM payments WHERE status = "declined"')
        declined_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'pending_count': pending_count,
            'approved_total': approved_total,
            'declined_count': declined_count
        }

    def update_user_balance_direct(self, user_id: int, new_balance: float):
        """Directly set user balance (for admin operations)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
        conn.commit()
        conn.close()

# Initialize database instance
db = Database()
