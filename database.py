import sqlite3
import os
from datetime import datetime
import time

def create_database():
    # Connect to SQLite database (creates it if not exists)
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()

    # Create users table based on the schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        firstname TEXT,
        lastname TEXT,
        email TEXT UNIQUE NOT NULL,
        is_verified BOOLEAN DEFAULT FALSE,
        chat_id INTEGER,
        telegram_username TEXT,
        secret_key TEXT,
        current_otp TEXT,
        otp_expiry FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Commit changes and close connection
    conn.commit()
    conn.close()

def add_user(user_data):
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO users (firstname, lastname, email, secret_key) 
            VALUES (?, ?, ?, ?)""",
            (user_data.get('firstname'), user_data.get('lastname'), 
             user_data['email'], user_data['secret_key'])
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT id, firstname, lastname, email, is_verified, 
            chat_id, telegram_username, secret_key, current_otp, otp_expiry 
            FROM users WHERE email = ?""",
            (email,)
        )
        columns = [col[0] for col in cursor.description]
        user = cursor.fetchone()
        if user:
            return dict(zip(columns, user))
        return None
    finally:
        conn.close()

def update_user_otp(email, otp, expiry_time):
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """UPDATE users 
            SET current_otp = ?, otp_expiry = ?
            WHERE email = ?""",
            (otp, expiry_time, email)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def update_user_telegram(email, chat_id, telegram_username):
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """UPDATE users 
            SET chat_id = ?, telegram_username = ?
            WHERE email = ?""",
            (chat_id, telegram_username, email)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

# Create database and tables when module is imported
create_database()
