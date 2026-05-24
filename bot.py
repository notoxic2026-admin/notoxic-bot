import telebot
import psycopg2 # Database အသစ်အတွက်
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

TOKEN = '8780973280:AAEbgwiKGCZacarCDzDjH2Wq4s4MAt_1IwU'
DATABASE_URL = 'postgresql://postgres:GyXjLVNoHouChUTuyQCvCnpTJPsQqKxM@postgres.railway.internal:5432/railway' # သင်ပေးခဲ့သောလင့်ခ်

bot = telebot.TeleBot(TOKEN)

# 🔐 ဝန်ထမ်း Passwords စာရင်း
STAFF_PASSWORDS = {"9999": "Admin (Owner)", "1234": "PA PA MAY", "1235": "Sandi"}
BURMESE_DIGITS = {'၀': '0', '၁': '1', '၂': '2', '၃': '3', '၄': '4', '၅': '5', '၆': '6', '၇': '7', '၈': '8', '၉': '9'}
EXPENSE_CATEGORIES = ["🍻 Drinks and Cigarettes", "🍔 Food", "📢 Marketing", "📅 Fix Monthly", "🧹 Generals"]
user_states = {}

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS store_expenses (
            id SERIAL PRIMARY KEY,
            date TEXT,
            staff_name TEXT,
            category TEXT,
            item_name TEXT,
            price REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ... (ကျန်တဲ့ UI functions များနှင့် Logic အကုန်လုံးမှာ အရင်အတိုင်းထားပါ)
# အရေးကြီးဆုံးမှာ save_expenses_to_db နှင့် view functions များရှိ sqlite3.connect() ကို get_db_connection() နဲ့ အစားထိုးပေးရပါမယ် ...

# (အောက်တွင် save_expenses_to_db ကို အပြောင်းအလဲလုပ်ထားပါသည်)
def save_expenses_to_db(message):
    chat_id = message.chat.id
    raw_text = message.text
    staff = user_states[chat_id]["staff_name"]
    date = user_states[chat_id]["chosen_date"]
    category = user_states[chat_id]["category"]
    prefix = user_states[chat_id].get("prefix_item", "")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    lines = raw_text.strip().split('\n')
    # ... (ကျန်တဲ့ logic အတိုင်း)
    # INSERT ပြီးရင် cursor.execute("SELECT lastval()") သို့မဟုတ် အသစ်ဝင်သွားတဲ့ ID ကိုယူပါ
    # ...
    conn.commit()
    conn.close()
    # ...
