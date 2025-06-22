# generate otp and send it to user via telegram
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

def get_db_connection():
    conn = sqlite3.connect('auth.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_chatid(chat_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE chat_id = ?",
            (chat_id,)
        )
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE telegram_username = ?",
            (username,)
        )
        user = cursor.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def update_user(username, chat_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE users 
            SET chat_id = ?, is_verified = TRUE
            WHERE telegram_username = ?""",
            (chat_id, username)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'{update.effective_user.username}: /start')
    
#     # Check if email was provided in the command
#     if context.args:
#         email = context.args[0]
#         username = update.effective_user.username
#         chat_id = update.effective_chat.id
        
#         # Update the user's chat_id and telegram_username
#         conn = get_db_connection()
#         try:
#             cursor = conn.cursor()
#             cursor.execute(
#                 """UPDATE users 
#                 SET chat_id = ?, telegram_username = ?, is_verified = TRUE
#                 WHERE email = ?""",
#                 (chat_id, username, email)
#             )
#             conn.commit()
#             if cursor.rowcount > 0:
#                 await update.message.reply_text(f'Account linked successfully! You can now use 2FA authentication.')
#             else:
#                 await update.message.reply_text(f'No account found with email: {email}')
#         except Exception as e:
#             print(e)
#             await update.message.reply_text('Error linking account. Please try again.')
#         finally:
#             conn.close()
#     else:
    await update.message.reply_text(
        f'Welcome to SecureAuth, {update.effective_user.first_name}!\n'
        f'To link your account, use the command: auth\n'
    )

async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f'{update.effective_user.username}: /auth')
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    
    user_exists = get_user_by_username(username)
    if not user_exists:
        await update.message.reply_text(f'Account not found')
    elif user_exists and not user_exists['chat_id']:
        print('linking account ...')
        result = update_user(username, chat_id)
        if result:
            await update.message.reply_text(f'Account linked successfully')
    elif user_exists and user_exists['chat_id'] == chat_id:
        await update.message.reply_text(f'You are already linked')
    elif user_exists and user_exists['chat_id'] != chat_id:
        await update.message.reply_text(f'Account already linked to another user')
    else:
        await update.message.reply_text(f'Error in linking account')

app = ApplicationBuilder().token(os.getenv('BOT_KEY')).build()

app.add_handler(CommandHandler("start", start_chat))
app.add_handler(CommandHandler("auth", link_account))

if __name__ == '__main__':
    # check database connection
    try:
        conn = get_db_connection()
        conn.cursor().execute("SELECT 1")
        print('Database connection successful')
        conn.close()
    except Exception as e:
        print('Database connection failed')
        print(e)
        exit(1)

    print('Bot running ...')
    app.run_polling()
    print('Bot stopped')
