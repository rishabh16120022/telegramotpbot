import sqlite3
import datetime
from typing import List, Tuple, Optional
import config

class Database:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path

    # ... (keep all existing methods) ...

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
        return payment

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

# Initialize database instance
db = Database()
