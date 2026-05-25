import telebot
import psycopg2
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

# --- Configuration ---
TOKEN = '8780973280:AAEbgwiKGCZacarCDzDjH2Wq4s4MAt_1IwU'
DATABASE_URL = 'postgresql://postgres:GyXjLVNoHouChUTuyQCvCnpTJPsQqKxM@postgres.railway.internal:5432/railway'

bot = telebot.TeleBot(TOKEN)

STAFF_PASSWORDS = {"9999": "Admin (Owner)", "1234": "PA PA MAY", "1235": "Sandi"}
EXPENSE_CATEGORIES = ["🍻 Drinks and Cigarettes", "🍔 Food", "📢 Marketing", "📅 Fix Monthly", "🧹 Generals"]
user_states = {}

# --- Database Setup ---
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

# --- Bot Handlers ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 မင်္ဂလာပါ။\nကျေးဇူးပြု၍ သင့်ရဲ့ လျှို့ဝှက်နံပါတ် (Password) ကို ရိုက်ထည့်ပါ။")
    bot.register_next_step_handler(message, check_password)

def check_password(message):
    chat_id = message.chat.id
    password = message.text.strip()
    
    if password in STAFF_PASSWORDS:
        staff_name = STAFF_PASSWORDS[password]
        user_states[chat_id] = {"staff_name": staff_name}
        bot.send_message(chat_id, f"✅ မှန်ကန်ပါတယ်။ {staff_name} အဖြစ် ဝင်ရောက်ပြီးပါပြီ။")
        show_main_menu(chat_id)
    else:
        msg = bot.send_message(chat_id, "❌ Password မှားနေပါတယ်။ ပြန်လည်ရိုက်ထည့်ပါ။")
        bot.register_next_step_handler(msg, check_password)

def show_main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("💸 စာရင်းအသစ် သွင်းမည်"), KeyboardButton("📊 အစီရင်ခံစာ ကြည့်မည်"))
    msg = bot.send_message(chat_id, "👇 အောက်ပါ လုပ်ဆောင်ချက်ကို ရွေးချယ်ပါ -", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_main_menu)

def handle_main_menu(message):
    chat_id = message.chat.id
    text = message.text
    
    if text == "💸 စာရင်းအသစ် သွင်းမည်":
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
        markup.add(KeyboardButton(today), KeyboardButton(yesterday))
        markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
        msg = bot.send_message(chat_id, "📅 နေ့စွဲ ရွေးချယ်ပါ -", reply_markup=markup)
        bot.register_next_step_handler(msg, choose_category)
        
    elif text == "📊 အစီရင်ခံစာ ကြည့်မည်":
        view_report(message)
    else:
        show_main_menu(chat_id)

def choose_category(message):
    chat_id = message.chat.id
    if message.text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
        
    user_states[chat_id]["chosen_date"] = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in EXPENSE_CATEGORIES:
        markup.add(KeyboardButton(cat))
    markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
    
    msg = bot.send_message(chat_id, "📂 ကုန်ကျစရိတ် အမျိုးအစား ရွေးပါ -", reply_markup=markup)
    bot.register_next_step_handler(msg, enter_expense_items)

def enter_expense_items(message):
    chat_id = message.chat.id
    if message.text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
        
    user_states[chat_id]["category"] = message.text
    bot.send_message(chat_id, "📝 စာရင်းများကို ရိုက်ထည့်ပါ။\nပုံစံ: ပစ္စည်းအမည်=စျေးနှုန်း\n(ဥပမာ - ကြက်ဥ=3000)\nစာကြောင်းခွဲပြီး အများကြီး တစ်ခါတည်း ရိုက်ထည့်လို့ရပါတယ်။")
    bot.register_next_step_handler(message, save_expenses_to_db)

def save_expenses_to_db(message):
    chat_id = message.chat.id
    raw_text = message.text
    
    if "staff_name" not in user_states.get(chat_id, {}):
        bot.send_message(chat_id, "ကျေးဇူးပြု၍ /start ကိုပြန်နှိပ်ပါ။")
        return

    staff = user_states[chat_id]["staff_name"]
    date = user_states[chat_id]["chosen_date"]
    category = user_states[chat_id]["category"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    lines = raw_text.strip().split('\n')
    saved_items = []
    
    for line in lines:
        if '=' in line:
            parts = line.split('=')
            item_name = parts[0].strip()
            try:
                price = float(parts[1].strip())
                # PostgreSQL မှာ ? အစား %s ကို အသုံးပြုရပါတယ်
                cursor.execute('''
                    INSERT INTO store_expenses (date, staff_name, category, item_name, price)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                ''', (date, staff, category, item_name, price))
                inserted_id = cursor.fetchone()[0]
                saved_items.append(f"[{inserted_id}] {item_name} = {price}")
            except ValueError:
                continue

    conn.commit()
    conn.close()
    
    if saved_items:
        reply = "✅ Database သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ:\n\n" + "\n".join(saved_items)
        bot.send_message(chat_id, reply)
        show_main_menu(chat_id)
    else:
        msg = bot.send_message(chat_id, "❌ ပုံစံမှားနေပါသည်။ ဥပမာ - 'ရေခဲသေတ္တာ=5000' ဟု ရိုက်ထည့်ပါ။")
        bot.register_next_step_handler(msg, save_expenses_to_db)

def view_report(message):
    chat_id = message.chat.id
    today = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, item_name, price, staff_name FROM store_expenses WHERE date = %s", (today,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(chat_id, f"📅 {today} အတွက် စာရင်း မရှိသေးပါ။")
    else:
        report = f"📊 {today} အတွက် အစီရင်ခံစာ\n\n"
        total = 0
        for row in rows:
            report += f"[{row[0]}] {row[1]} - {row[2]} = {row[3]} ({row[4]})\n"
            total += row[3]
        report += f"\n💰 စုစုပေါင်း = {total}"
        bot.send_message(chat_id, report)
        
    show_main_menu(chat_id)

bot.polling(none_stop=True)
