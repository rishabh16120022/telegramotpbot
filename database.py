import sqlite3
import datetime
from typing import List, Tuple, Optional
import config

class Database:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path

    # ... (keep all existing methods) ...

    def create_otp_purchase(self, user_id: int, account_type: str, phone_number: str, price: float):
        """Create a new OTP purchase with pending status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO account_orders (user_id, account_type, phone_number, status, price) 
            VALUES (?, ?, ?, 'pending', ?)
        ''', (user_id, account_type, phone_number, price))
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id

    def get_pending_otp_order(self, user_id: int):
        """Get user's pending OTP order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM account_orders 
            WHERE user_id = ? AND status = 'pending' 
            ORDER BY purchased_at DESC LIMIT 1
        ''', (user_id,))
        order = cursor.fetchone()
        conn.close()
        return order

    def update_otp_code(self, order_id: int, otp_code: str):
        """Update OTP code for an order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE account_orders 
            SET otp_code = ?, status = 'otp_ready' 
            WHERE id = ?
        ''', (otp_code, order_id))
        conn.commit()
        conn.close()

    def complete_otp_order(self, order_id: int):
        """Mark OTP order as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE account_orders 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (order_id,))
        conn.commit()
        conn.close()

    def cancel_otp_order(self, order_id: int):
        """Cancel OTP order and refund"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get order details
        cursor.execute('SELECT user_id, price FROM account_orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        
        if order:
            user_id, price = order
            # Update order status
            cursor.execute('''
                UPDATE account_orders 
                SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP, refund_amount = ? 
                WHERE id = ?
            ''', (price, order_id))
            
            # Refund user balance
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (price, user_id))
            cursor.execute('UPDATE users SET total_refund = total_refund + ? WHERE user_id = ?', (price, user_id))
        
        conn.commit()
        conn.close()
        return order

    def get_available_phone_number(self, account_type: str):
        """Get a random available phone number"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT phone_number FROM accounts 
            WHERE type = ? AND status = 'available' 
            ORDER BY RANDOM() LIMIT 1
        ''', (account_type,))
        result = cursor.fetchone()
        
        if result:
            phone_number = result[0]
            # Mark as in use
            cursor.execute('UPDATE accounts SET status = "in_use" WHERE phone_number = ?', (phone_number,))
            conn.commit()
        
        conn.close()
        return phone_number if result else None

    def release_phone_number(self, phone_number: str):
        """Release phone number back to available pool"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE accounts SET status = "available" WHERE phone_number = ?', (phone_number,))
        conn.commit()
        conn.close()

    def mark_phone_sold(self, phone_number: str, user_id: int):
        """Mark phone number as sold"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE accounts SET status = "sold" WHERE phone_number = ?', (phone_number,))
        cursor.execute('UPDATE users SET accounts_bought = accounts_bought + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def get_user_active_orders(self, user_id: int):
        """Get user's active OTP orders"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM account_orders 
            WHERE user_id = ? AND status IN ('pending', 'otp_ready')
            ORDER BY purchased_at DESC
        ''', (user_id,))
        orders = cursor.fetchall()
        conn.close()
        return orders

# Initialize database instance
db = Database()
