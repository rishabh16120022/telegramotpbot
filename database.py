import sqlite3
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

db = Database()
