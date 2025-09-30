import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []

# Payment Configuration
MIN_DEPOSIT = int(os.getenv('MIN_DEPOSIT', 50))
OWNER_QR_CODE = os.getenv('OWNER_QR_CODE', "https://example.com/owner_qr.jpg")

# Account Prices
TELEGRAM_OTP_PRICE = int(os.getenv('TELEGRAM_OTP_PRICE', 10))
WHATSAPP_OTP_PRICE = int(os.getenv('WHATSAPP_OTP_PRICE', 15))
SESSION_PRICE = int(os.getenv('SESSION_PRICE', 25))

# Database
DB_NAME = os.getenv('DB_NAME', 'accounts_bot.db')
DB_PATH = DB_NAME

def init_database():
    """Initialize database with proper path"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0,
            total_spent REAL DEFAULT 0,
            accounts_bought INTEGER DEFAULT 0,
            is_blocked BOOLEAN DEFAULT FALSE,
            is_admin BOOLEAN DEFAULT FALSE,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_refund REAL DEFAULT 0
        )
    ''')
    
    # Accounts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            phone_number TEXT UNIQUE,
            otp_code TEXT,
            status TEXT DEFAULT 'available',
            price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Account orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            account_type TEXT,
            phone_number TEXT,
            otp_code TEXT,
            status TEXT DEFAULT 'pending',
            price REAL,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            refund_amount REAL DEFAULT 0
        )
    ''')
    
    # Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            utr TEXT,
            status TEXT DEFAULT 'pending',
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert owner if not exists
    if OWNER_ID:
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username, is_admin) VALUES (?, ?, ?)', 
                      (OWNER_ID, "Owner", True))
    
    conn.commit()
    conn.close()

# Initialize database on import
init_database()
