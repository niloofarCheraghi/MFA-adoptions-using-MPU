from flask import (
    Flask, request, jsonify, render_template, 
    redirect, url_for, flash, session
)
import pyotp
import time
import random
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import os
from telegram import Bot
from database import (
    get_user_by_email,
    add_user,
    update_user_otp,
    update_user_telegram
)
from functools import wraps
import asyncio

# configure connections
load_dotenv()
async def send_telegram_message(chat_id,text):
    bot = Bot(token=os.getenv('BOT_KEY'))
    await bot.send_message(chat_id=chat_id, text=text)

def send_message_sync(chat_id, text):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # This might happen in development tools (e.g., in Jupyter or threaded server)
        asyncio.ensure_future(send_telegram_message(chat_id, text))
    else:
        loop.run_until_complete(send_telegram_message(chat_id, text))


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# random otp for telegram
def generate_otp():
    return str(random.randint(100000, 999999))

def generate_secret_key():
    return pyotp.random_base32()

# function to verify otp
def verify_otp(secret_key: str, otp: str) -> bool:
    totp = pyotp.TOTP(secret_key, interval=300)
    print(totp.now())
    return totp.verify(otp)

def get_gravatar_hash(email):
    return hashlib.md5(email.lower().strip().encode()).hexdigest()

@app.template_filter('md5')
def md5_filter(s):
    return hashlib.md5(s.encode()).hexdigest()

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    user_data = request.form
    if not user_data or not user_data.get('email'):
        flash('Invalid registration data', 'danger')
        return redirect(url_for('register'))

    # check if user already exists
    existing_user = get_user_by_email(user_data['email'])
    if existing_user:
        flash('Email already registered', 'danger')
        return redirect(url_for('register'))
    
    # generate otp secret
    secret_key = generate_secret_key()
    user_dict = {
        'firstname': user_data['firstname'],
        'lastname': user_data['lastname'],
        'email': user_data['email'],
        'telegram_username': user_data['telegram_username'],
        'secret_key': secret_key
    }

    # save the user to the database
    if add_user(user_dict):
        success_message = (
            f'Registration successful!\n\n'
            f'1. Please set up your authenticator app with this secret key:\n{secret_key}\n\n'
            f'2. Link your Telegram account:\n'
            f'   - Open Telegram and search for @secure_auth2fa_bot\n'
            f'   - Start a chat with the bot\n'
            f'   - Send the command: /start {user_data["email"]}'
        )
        flash(success_message, 'success')
        return redirect(url_for('login'))
    else:
        flash('Failed to register user', 'danger')
        return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.form
    if not data or not all(k in data for k in ['email', 'telegram_otp', 'secret_otp']):
        flash('Please fill in all fields', 'danger')
        return redirect(url_for('login'))

    user = get_user_by_email(data['email'])
    if not user or not user['chat_id']:
        flash('User not found or not linked to telegram', 'danger')
        return redirect(url_for('login'))
    
    if user.get('otp_expiry', 0) < time.time():
        flash('OTP has expired. Please request a new one.', 'danger')
        return redirect(url_for('login'))

    if user['current_otp'] == data['telegram_otp'] and verify_otp(user['secret_key'], data['secret_otp']):
        session['user_email'] = user['email']
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid OTPs', 'danger')
        return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_user_by_email(session['user_email'])
    if not user:
        session.clear()
        flash('User not found', 'danger')
        return redirect(url_for('login'))
    
    # Add created_at in readable format
    if isinstance(user.get('created_at'), (int, float)):
        user['created_at'] = datetime.fromtimestamp(user['created_at']).strftime('%B %d, %Y')
    
    return render_template('dashboard.html', user=user)



@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# API endpoints for AJAX calls
@app.route('/otp', methods=['GET'])
def get_otp():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not user['chat_id']:
        return jsonify({'error': 'User not linked to telegram'}), 404
    
    # generate otp
    otp = generate_otp()
    # save the otp to database and set expiry time to 5 mins
    if update_user_otp(email, otp, time.time() + 300):
        try:
            # Using sync version since Flask doesn't handle async well by default
            # asyncio.run(bot.send_message(chat_id=user['chat_id'], text=f'Your otp is {otp}'))
            # bot.send_message(chat_id=user['chat_id'], text=f'Your otp is {otp}')
            send_message_sync(user['chat_id'], f'Your OTP is {otp}')
            return jsonify({'message': f'OTP sent successfully to your Telegram account'})
        except Exception as e:
            print(f'Error sending OTP: {e}')      
            return jsonify({'error': 'Failed to send OTP'}), 500
    else:
        return jsonify({'error': 'Failed to generate OTP'}), 500


if __name__ == '__main__':
    app.run(debug=True)
