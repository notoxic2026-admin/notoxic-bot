import telebot
import sqlite3
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

TOKEN = '8780973280:AAEbgwiKGCZacarCDzDjH2Wq4s4MAt_1IwU'
bot = telebot.TeleBot(TOKEN)

# 🔐 ဝန်ထမ်း Passwords စာရင်း
STAFF_PASSWORDS = {
    "9999": "Admin (Owner)",
    "1234": "PA PA MAY",
    "1235": "Sandi"
}

BURMESE_DIGITS = {
    '၀': '0', '၁': '1', '၂': '2', '၃': '3', '၄': '4',
    '၅': '5', '၆': '6', '၇': '7', '၈': '8', '၉': '9'
}

EXPENSE_CATEGORIES = ["🍻 Drinks and Cigarettes", "🍔 Food", "📢 Marketing", "📅 Fix Monthly", "🧹 Generals"]

user_states = {}

def init_db():
    conn = sqlite3.connect('notoxic_expenses.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS store_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

def show_main_menu(chat_id, staff_name):
    user_states[chat_id] = {"state": "MAIN_MENU", "staff_name": staff_name}
    
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_expense = KeyboardButton("💸 စာရင်းအသစ် သွင်းမည်")
    btn_report = KeyboardButton("📊 အစီရင်ခံစာ စစ်ဆေးမည် (Report)")
    btn_change_user = KeyboardButton("🔄 ဝန်ထမ်း/အကောင့် ပြောင်းမည်")
    
    markup.add(btn_expense, btn_report)
    
    if staff_name == "Admin (Owner)":
        markup.add(KeyboardButton("❌ စာရင်းဖျက်ရန် (Admin Only)"), KeyboardButton("✏️ စာရင်းပြင်ရန် (Admin Only)"))
    
    markup.add(btn_change_user)
        
    bot.send_message(chat_id, f"🏠 [ {staff_name} ] ပင်မစာမျက်နှာသို့ ရောက်ရှိနေပါသည်။ \nပြုလုပ်လိုသည့် လုပ်ငန်းစဉ်ကို ရွေးချယ်ပါ။", reply_markup=markup)

def ask_for_entry_type(chat_id):
    user_states[chat_id]["state"] = "SELECTING_ENTRY_TYPE"
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(
        KeyboardButton("💸 ဆိုင်သုံး အသုံးစရိတ် (Expense)"),
        KeyboardButton("🍽️ ဝန်ထမ်းအကြွေးစာရင်း (Staff Credit)"),
        KeyboardButton("⬅️ နောက်သို့ (Back)")
    )
    bot.send_message(chat_id, "👉 မည်သည့် စာရင်းအမျိုးအစားကို သွင်းချင်ပါသလဲ ခင်ဗျာ။", reply_markup=markup)

def ask_for_date(chat_id):
    user_states[chat_id]["state"] = "SELECTING_DATE"
    today_str = datetime.now().strftime("%d/%m/%Y")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(
        KeyboardButton(f"🗓️ ဒီနေ့ ({today_str})"), 
        KeyboardButton(f"⏪ မနေ့က ({yesterday_str})"),
        KeyboardButton("✏️ အခြားရက်စွဲ ကိုယ်တိုင်ရိုက်မည်"),
        KeyboardButton("⬅️ နောက်သို့ (Back)")
    )
    bot.send_message(chat_id, "🗓️ ဤစာရင်းက မည်သည့်ရက်စွဲအတွက်လဲ ခင်ဗျာ။", reply_markup=markup)

def ask_for_category(chat_id):
    user_states[chat_id]["state"] = "SELECTING_CATEGORY"
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for cat in EXPENSE_CATEGORIES:
        markup.add(KeyboardButton(cat))
    markup.add(KeyboardButton("⬅️ နောက်သို့ (Back)"))
    bot.send_message(chat_id, "🗂️ မည်သည့် အသုံးစရိတ် အမျိုးအစားအတွက် စာရင်းသွင်းမလဲ ခင်ဗျာ။", reply_markup=markup)

def ask_for_staff_credit_person(chat_id):
    user_states[chat_id]["state"] = "SELECTING_CREDIT_PERSON"
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(
        KeyboardButton("🧑‍💻 AMK"),
        KeyboardButton("👩‍💻 PA PA MAY"),
        KeyboardButton("👩‍💻 Sandi"),
        KeyboardButton("⬅️ နောက်သို့ (Back)")
    )
    bot.send_message(chat_id, "🍽️ မည်သူ စားသောက်ထားသည့် စာရင်းဖြစ်ပါသလဲ ခင်ဗျာ။", reply_markup=markup)

def ask_for_input_data(chat_id, category, prefix_item=""):
    user_states[chat_id]["state"] = "INPUT_DATA"
    user_states[chat_id]["category"] = category
    user_states[chat_id]["prefix_item"] = prefix_item
    
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(KeyboardButton("⬅️ နောက်သို့ (Back)"))
    
    example = "Singha=100*3"
    bot.send_message(chat_id, f"📝 [{category}] အတွက် စာရင်းများကို ရိုက်ထည့်ပေးပါဗျာ။\n\n(ဥပမာ -\n{example})", reply_markup=markup)

def show_report_menu(chat_id):
    user_states[chat_id]["state"] = "SELECTING_REPORT_TYPE"
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(
        KeyboardButton("📅 နေ့စဉ်ချုပ် (Daily Report)"),
        KeyboardButton("📅 အပတ်စဉ်ချုပ် (Weekly Report)"),
        KeyboardButton("📅 လချုပ် (Monthly Report)"),
        KeyboardButton("⬅️ နောက်သို့ (Back)")
    )
    bot.send_message(chat_id, "📊 ဘယ်လို အစီရင်ခံစာမျိုး စစ်ဆေးချင်ပါသလဲ ခင်ဗျာ။", reply_markup=markup)

# 📊 လချုပ်အတွက် Total သို့မဟုတ် Detail ရွေးခိုင်းသည့် UI
def show_monthly_report_options(chat_id):
    user_states[chat_id]["state"] = "SELECTING_MONTHLY_REPORT_OPTION"
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(
        KeyboardButton("📊 အနှစ်ချုပ်ကြည့်မည် (Total)"),
        KeyboardButton("📝 အသေးစိတ်ကြည့်မည် (Detail)"),
        KeyboardButton("⬅️ နောက်သို့ (Back)")
    )
    bot.send_message(chat_id, "👉 လချုပ်ကို မည်သို့ စစ်ဆေးလိုပါသလဲ ခင်ဗျာ။", reply_markup=markup)

# 🔎 Detail အတွက် Expense သို့မဟုတ် Credit သီးသန့်ရွေးခိုင်းသည့် UI
def show_detail_type_options(chat_id):
    user_states[chat_id]["state"] = "SELECTING_DETAIL_TYPE"
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(
        KeyboardButton("💸 ဆိုင်သုံး အသုံးစရိတ် အသေးစိတ် (Expense Detail)"),
        KeyboardButton("🍽️ ဝန်ထမ်းအကြွေး အသေးစိတ် (Credit Detail)"),
        KeyboardButton("⬅️ နောက်သို့ (Back)")
    )
    bot.send_message(chat_id, "🔎 ဘယ်အမျိုးအစားရဲ့ အသေးစိတ်စာရင်းကို ကြည့်ချင်ပါသလဲ ခင်ဗျာ။", reply_markup=markup)

def logout_user(chat_id):
    user_states[chat_id] = {"state": "AWAITING_PASSWORD"}
    bot.send_message(chat_id, "🔄 စနစ်ထဲမှ ထွက်ပြီးပါပြီ။ \n\nကျေးဇူးပြု၍ အကောင့်အသစ်၏ လျှို့ဝှက်နံပါတ် (Password) ကို ရိုက်ထည့်ပေးပါရန်။", reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_states[chat_id] = {"state": "AWAITING_PASSWORD"}
    bot.send_message(chat_id, "🔐 No Toxic Account မှ ကြိုဆိုပါတယ်။ \n\nရှေ့ဆက်ရန် သင့်၏ လျှို့ဝှက်နံပါတ် (Password) ကို ရိုက်ထည့်ပေးပါရန်။")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get("state") == "AWAITING_PASSWORD")
def check_password(message):
    chat_id = message.chat.id
    password = message.text.strip()
    
    if password in STAFF_PASSWORDS:
        staff_name = STAFF_PASSWORDS[password]
        show_main_menu(chat_id, staff_name)
    else:
        bot.send_message(chat_id, "❌ လျှို့ဝှက်နံပါတ် မှားယွင်းနေပါသည်။ \nကျေးဇူးပြု၍ ပြန်လည်ရိုက်ထည့်ပေးပါရန်။")

@bot.message_handler(func=lambda msg: True)
def handle_navigation(message):
    chat_id = message.chat.id
    text = message.text
    
    if chat_id not in user_states:
        return

    current_state = user_states[chat_id].get("state")
    staff_name = user_states[chat_id].get("staff_name")
    entry_type = user_states[chat_id].get("entry_type", "EXPENSE")

    if text == "⬅️ နောက်သို့ (Back)":
        if current_state in ["SELECTING_DATE", "SELECTING_REPORT_TYPE", "DELETE_ASK_DATE", "EDIT_ASK_DATE", "SELECTING_ENTRY_TYPE", "SELECTING_MONTHLY_REPORT_OPTION"]:
            show_main_menu(chat_id, staff_name)
        elif current_state == "SELECTING_DETAIL_TYPE":
            show_monthly_report_options(chat_id)
        elif current_state in ["SELECTING_CATEGORY", "SELECTING_CREDIT_PERSON", "CUSTOM_DATE_INPUT", "REPORT_CUSTOM_DATE", "DELETE_CHOOSE_ID"]:
            if current_state == "DELETE_CHOOSE_ID":
                show_main_menu(chat_id, staff_name)
            else:
                ask_for_date(chat_id)
        elif current_state in ["INPUT_DATA", "EDIT_CHOOSE_ID", "EDIT_INPUT_NEW_PRICE"]:
            if current_state == "INPUT_DATA" and entry_type == "CREDIT":
                ask_for_staff_credit_person(chat_id)
            elif current_state == "INPUT_DATA" and entry_type == "EXPENSE":
                ask_for_category(chat_id)
            else:
                show_main_menu(chat_id, staff_name)
        return

    if text == "🔄 ဝန်ထမ်း/အကောင့် ပြောင်းမည်":
        logout_user(chat_id)
        return

    # --- MAIN MENU NAV ---
    if current_state == "MAIN_MENU":
        if text == "💸 စာရင်းအသစ် သွင်းမည်":
            ask_for_entry_type(chat_id)
        elif text == "📊 အစီရင်ခံစာ စစ်ဆေးမည် (Report)":
            show_report_menu(chat_id)
        elif text == "❌ စာရင်းဖျက်ရန် (Admin Only)" and staff_name == "Admin (Owner)":
            user_states[chat_id]["state"] = "DELETE_ASK_DATE"
            markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            markup.add(KeyboardButton("⬅️ နောက်သို့ (Back)"))
            bot.send_message(chat_id, "❌ **[စာရင်းဖျက်ခြင်း]** \nဘယ်ရက်စွဲက စာရင်းကို ဖျက်ချင်ပါသလဲ ခင်ဗျာ။ (ဥပမာ - `19/05/2026`)", reply_markup=markup)
        elif text == "✏️ စာရင်းပြင်ရန် (Admin Only)" and staff_name == "Admin (Owner)":
            user_states[chat_id]["state"] = "EDIT_ASK_DATE"
            markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            markup.add(KeyboardButton("⬅️ နောက်သို့ (Back)"))
            bot.send_message(chat_id, "✏️ **[စာရင်းပြင်ခြင်း]** \nဘယ်ရက်စွဲက စာရင်းကို ပြင်ချင်ပါသလဲ ခင်ဗျာ။ (ဥပမာ - `19/05/2026`)", reply_markup=markup)
            
    elif current_state == "SELECTING_ENTRY_TYPE":
        if text == "💸 ဆိုင်သုံး အသုံးစရိတ် (Expense)":
            user_states[chat_id]["entry_type"] = "EXPENSE"
            ask_for_date(chat_id)
        elif text == "🍽️ ဝန်ထမ်းအကြွေးစာရင်း (Staff Credit)":
            user_states[chat_id]["entry_type"] = "CREDIT"
            ask_for_date(chat_id)

    elif current_state == "DELETE_ASK_DATE":
        if re.match(r'^\d{2}/\d{2}/\d{4}$', text.strip()):
            target_date = text.strip()
            conn = sqlite3.connect('notoxic_expenses.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, category, item_name, price FROM store_expenses WHERE date = ?", (target_date,))
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                bot.send_message(chat_id, f"📋 {target_date} ရက်နေ့အတွက် ဖျက်စရာစာရင်း မရှိပါဘူးဗျာ။")
                show_main_menu(chat_id, staff_name)
                return
                
            msg_list = f"❌ **{target_date} ရှိ စာရင်းများ -**\n\n"
            for row in rows:
                msg_list += f"🆔 /del_{row[0]} | [{row[1]}] {row[2]} = {row[3]:,.0f}\n"
            msg_list += "\nဖျက်လိုသော စာရင်း၏ ရှေ့က 🆔 လင့်ခ်လေးကို နှိပ်ပေးပါဗျာ။"
            
            user_states[chat_id]["state"] = "DELETE_CHOOSE_ID"
            bot.send_message(chat_id, msg_list)
        else:
            bot.send_message(chat_id, "❌ ရက်စွဲပုံစံမမှန်ပါ။ `နေ့/လ/ခုနှစ်` အတိုင်း ပြန်ရိုက်ပါ။")

    elif current_state == "EDIT_ASK_DATE":
        if re.match(r'^\d{2}/\d{2}/\d{4}$', text.strip()):
            target_date = text.strip()
            conn = sqlite3.connect('notoxic_expenses.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, category, item_name, price FROM store_expenses WHERE date = ?", (target_date,))
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                bot.send_message(chat_id, f"📋 {target_date} ရက်နေ့အတွက် ပြင်စရာစာရင်း မရှိပါဘူးဗျာ။")
                show_main_menu(chat_id, staff_name)
                return
                
            msg_list = f"✏️ **{target_date} ရှိ စာရင်းများ -**\n\n"
            for row in rows:
                msg_list += f"🆔 /edit_{row[0]} | [{row[1]}] {row[2]} = {row[3]:,.0f}\n"
            msg_list += "\nပြင်လိုသော စာရင်း၏ ရှေ့က 🆔 လင့်ခ်လေးကို နှိပ်ပေးပါဗျာ။"
            
            user_states[chat_id]["state"] = "EDIT_CHOOSE_ID"
            bot.send_message(chat_id, msg_list)
        else:
            bot.send_message(chat_id, "❌ ရက်စွဲပုံစံမမှန်ပါ။ `နေ့/လ/ခုနှစ်` အတိုင်း ပြန်ရိုက်ပါ။")

    elif current_state == "EDIT_INPUT_NEW_PRICE":
        for mm_char, eng_char in BURMESE_DIGITS.items():
            text = text.replace(mm_char, eng_char)
        try:
            new_price = float(re.sub(r'[^\d.]', '', text))
            record_id = user_states[chat_id]["edit_id"]
            
            conn = sqlite3.connect('notoxic_expenses.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE store_expenses SET price = ? WHERE id = ?", (new_price, record_id))
            conn.commit()
            conn.close()
            
            bot.send_message(chat_id, f"✅ စာရင်းပြင်ဆင်ခြင်း အောင်မြင်ပါသည်။ စျေးနှုန်းအသစ်ကို `{new_price:,.0f}` သို့ ပြောင်းလဲလိုက်ပါပြီ။")
            show_main_menu(chat_id, staff_name)
        except:
            bot.send_message(chat_id, "❌ ဂဏန်းအမှန်အတိုင်း သေချာပြန်ရိုက်ပေးပါဗျာ။")

    elif current_state == "SELECTING_REPORT_TYPE":
        if text == "📅 နေ့စဉ်ချုပ် (Daily Report)":
            user_states[chat_id]["state"] = "REPORT_CUSTOM_DATE"
            markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            markup.add(KeyboardButton("⬅️ နောက်သို့ (Back)"))
            bot.send_message(chat_id, "🔍 ဘယ်ရက်စွဲအတွက် ရက်ချုပ်ကြည့်ချင်ပါသလဲ ခင်ဗျာ။ (ဥပမာ - `19/05/2026`)", reply_markup=markup)
        elif text == "📅 အပတ်စဉ်ချုပ် (Weekly Report)":
            view_weekly_report(chat_id)
        elif text == "📅 လချုပ် (Monthly Report)":
            show_monthly_report_options(chat_id)

    elif current_state == "SELECTING_MONTHLY_REPORT_OPTION":
        if text == "📊 အနှစ်ချုပ်ကြည့်မည် (Total)":
            view_monthly_total_report(chat_id)
        elif text == "📝 အသေးစိတ်ကြည့်မည် (Detail)":
            show_detail_type_options(chat_id)

    elif current_state == "SELECTING_DETAIL_TYPE":
        if text == "💸 ဆိုင်သုံး အသုံးစရိတ် အသေးစိတ် (Expense Detail)":
            view_monthly_detailed_report(chat_id, detail_type="EXPENSE")
        elif text == "🍽️ ဝန်ထမ်းအကြွေး အသေးစိတ် (Credit Detail)":
            view_monthly_detailed_report(chat_id, detail_type="CREDIT")

    elif current_state == "REPORT_CUSTOM_DATE":
        if re.match(r'^\d{2}/\d{2}/\d{4}$', text.strip()):
            view_daily_report(chat_id, text.strip())
        else:
            bot.send_message(chat_id, "❌ ရက်စွဲပုံစံ မမှန်ပါ။ `နေ့/လ/ခုနှစ်` အတိုင်း ပြန်ရိုက်ပေးပါဗျာ။")

    elif current_state == "SELECTING_DATE":
        chosen_date = ""
        if "ဒီနေ့" in text:
            chosen_date = datetime.now().strftime("%d/%m/%Y")
        elif "မနေ့က" in text:
            chosen_date = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        elif text == "✏️ အခြားရက်စွဲ ကိုယ်တိုင်ရိုက်မည်":
            user_states[chat_id]["state"] = "CUSTOM_DATE_INPUT"
            markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            markup.add(KeyboardButton("⬅️ နောက်သို့ (Back)"))
            bot.send_message(chat_id, "⌨️ ရက်စွဲကို `နေ့/လ/ခုနှစ်` ပုံစံအတိုင်း ရိုက်ထည့်ပေးပါဗျာ။ (ဥပမာ - `15/05/2026`)", reply_markup=markup)
            return

        if chosen_date:
            user_states[chat_id]["chosen_date"] = chosen_date
            if entry_type == "CREDIT":
                ask_for_staff_credit_person(chat_id)
            else:
                ask_for_category(chat_id)

    elif current_state == "CUSTOM_DATE_INPUT":
        if re.match(r'^\d{2}/\d{2}/\d{4}$', text.strip()):
            user_states[chat_id]["chosen_date"] = text.strip()
            if entry_type == "CREDIT":
                ask_for_staff_credit_person(chat_id)
            else:
                ask_for_category(chat_id)
        else:
            bot.send_message(chat_id, "❌ ရက်စွဲပုံစံ မမှန်ပါ။ ဥပမာ - `15/05/2026` အတိုင်း ပြန်ရိုက်ပေးပါဗျာ။")

    elif current_state == "SELECTING_CATEGORY":
        if text in EXPENSE_CATEGORIES:
            ask_for_input_data(chat_id, text)

    elif current_state == "SELECTING_CREDIT_PERSON":
        if text in ["🧑‍💻 AMK", "👩‍💻 PA PA MAY", "👩‍💻 Sandi"]:
            clean_name = text.replace("🧑‍💻 ", "").replace("👩‍💻 ", "")
            ask_for_input_data(chat_id, "🍽️ Staff Credit", prefix_item=f"({clean_name}) ")

    elif current_state == "INPUT_DATA":
        save_expenses_to_db(message)

@bot.message_handler(func=lambda msg: msg.text.startswith('/del_'))
def handle_delete_command(message):
    chat_id = message.chat.id
    if user_states.get(chat_id, {}).get("state") == "DELETE_CHOOSE_ID":
        try:
            record_id = int(message.text.split('_')[1])
            conn = sqlite3.connect('notoxic_expenses.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM store_expenses WHERE id = ?", (record_id,))
            conn.commit()
            conn.close()
            
            bot.send_message(chat_id, f"✅ စာရင်း ID {record_id} ကို Database ထဲကနေ လုံးဝ ဖျက်ပစ်လိုက်ပါပြီဗျာ။")
            show_main_menu(chat_id, user_states[chat_id]["staff_name"])
        except:
            bot.send_message(chat_id, "❌ ဖျက်ခြင်း မအောင်မြင်ပါ။ စာရင်းပြန်စစ်ပေးပါ။")

@bot.message_handler(func=lambda msg: msg.text.startswith('/edit_'))
def handle_edit_command(message):
    chat_id = message.chat.id
    if user_states.get(chat_id, {}).get("state") == "EDIT_CHOOSE_ID":
        try:
            record_id = int(message.text.split('_')[1])
            user_states[chat_id]["edit_id"] = record_id
            user_states[chat_id]["state"] = "EDIT_INPUT_NEW_PRICE"
            
            bot.send_message(chat_id, f"✍️ စာရင်း ID {record_id} အတွက် **စျေးနှုန်းအသစ်** ကို ရိုက်ထည့်ပေးပါဗျာ။")
        except:
            bot.send_message(chat_id, "❌ မှားယွင်းနေပါသည်။")

def save_expenses_to_db(message):
    chat_id = message.chat.id
    raw_text = message.text
    staff = user_states[chat_id]["staff_name"]
    date = user_states[chat_id]["chosen_date"]
    category = user_states[chat_id]["category"]
    prefix = user_states[chat_id].get("prefix_item", "")
    
    conn = sqlite3.connect('notoxic_expenses.db')
    cursor = conn.cursor()
    lines = raw_text.strip().split('\n')
    summary_lines = []
    total_cost = 0
    
    for line in lines:
        if "=" in line:
            item_name, price_str = line.split("=")
            item_name = prefix + item_name.strip()
            price_str = price_str.strip()
            
            for mm_char, eng_char in BURMESE_DIGITS.items():
                price_str = price_str.replace(mm_char, eng_char)
            
            try:
                if "*" in price_str:
                    parts = price_str.split("*")
                    num1 = float(re.sub(r'[^\d.]', '', parts[0]))
                    num2 = float(re.sub(r'[^\d.]', '', parts[1]))
                    price = num1 * num2
                else:
                    price = float(re.sub(r'[^\d.]', '', price_str))
                
                total_cost += price
                cursor.execute("INSERT INTO store_expenses (date, staff_name, category, item_name, price) VALUES (?, ?, ?, ?, ?)", (date, staff, category, item_name, price))
                summary_lines.append(f"• {item_name} = {price:,.0f}")
            except Exception:
                continue

    conn.commit()
    conn.close()
    
    reply_msg = f"No Toxic Account 🤖\n✅ {date} အတွက် [{category}] စာရင်းကို Database ထဲ သိမ်းဆည်းပြီးပါပြီ။\n\n📊 **ယနေ့ စာရင်းအနှစ်ချုပ်:**\n"
    reply_msg += "\n".join(summary_lines)
    reply_msg += f"\n\n💰 **စုစုပေါင်း = {total_cost:,.0f}**"
    
    bot.send_message(chat_id, reply_msg)
    show_main_menu(chat_id, staff)

def view_daily_report(chat_id, target_date):
    staff_name = user_states[chat_id]["staff_name"]
    conn = sqlite3.connect('notoxic_expenses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT category, item_name, price, staff_name FROM store_expenses WHERE date = ?", (target_date,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(chat_id, f"📋 {target_date} ရက်နေ့အတွက် ဘာစာရင်းမှ ရှာမတွေ့ပါဘူးဗျာ။")
        return
        
    report_msg = f"No Toxic Account 🤖\n📋 ရက်ချုပ် စစ်ဆေးမှု ရလဒ် ({target_date})-\n\n"
    grand_total = 0
    for row in rows:
        cat, item, price, staff = row
        if cat == "🍽️ Staff Credit" and staff_name != "Admin (Owner)" and f"({staff_name})" not in item:
            continue
        grand_total += price
        report_msg += f"• [{cat}] {item} = {price:,.0f} (by {staff})\n"
        
    report_msg += f"\n💰 **စုစုပေါင်း = {grand_total:,.0f}**"
    bot.send_message(chat_id, report_msg)
    show_main_menu(chat_id, staff_name)

def view_weekly_report(chat_id):
    staff_name = user_states[chat_id]["staff_name"]
    conn = sqlite3.connect('notoxic_expenses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT date, category, item_name, price FROM store_expenses")
    rows = cursor.fetchall()
    conn.close()
    
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)
    weekly_total = 0
    cat_totals = {}
    
    for row in rows:
        date_str, cat, item, price = row
        try:
            row_date = datetime.strptime(date_str, "%d/%m/%Y")
            if seven_days_ago <= row_date <= today:
                if cat == "🍽️ Staff Credit" and staff_name != "Admin (Owner)" and f"({staff_name})" not in item:
                    continue
                weekly_total += price
                cat_totals[cat] = cat_totals.get(cat, 0) + price
        except:
            continue
            
    if weekly_total == 0:
        bot.send_message(chat_id, "📋 လွန်ခဲ့သော ၇ ရက်အတွင်း မည်သည့် စာရင်းမှ မရှိသေးပါခင်ဗျာ။")
        return
        
    report_msg = f"No Toxic Account 🤖\n📊 **အပတ်စဉ်ချုပ် အစီရင်ခံစာ (Weekly Report)**\n\n"
    for cat, total in cat_totals.items():
        report_msg += f"• {cat} = {total:,.0f}\n"
    report_msg += f"\n💰 **၇ ရက်စာ စုစုပေါင်း = {weekly_total:,.0f}**"
    bot.send_message(chat_id, report_msg)
    show_main_menu(chat_id, staff_name)

# 📊 (Total) ခလုတ်အတွက်- အကျဉ်းချုပ်ပြသပေးမည့်စနစ်
def view_monthly_total_report(chat_id):
    staff_name = user_states[chat_id]["staff_name"]
    current_month_year = datetime.now().strftime("/%m/%Y")
    conn = sqlite3.connect('notoxic_expenses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT category, item_name, price FROM store_expenses WHERE date LIKE ?", ('%' + current_month_year,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(chat_id, f"📋 ယခုလ အတွက် စာရင်းမရှိသေးပါခင်ဗျာ။")
        return
        
    actual_expense_total = 0  
    staff_credit_total = 0    
    cat_totals = {}
    staff_credits = {"AMK": 0, "PA PA MAY": 0, "Sandi": 0}
    
    for row in rows:
        cat, item, price = row
        if cat in EXPENSE_CATEGORIES:
            actual_expense_total += price
            cat_totals[cat] = cat_totals.get(cat, 0) + price
        elif cat == "🍽️ Staff Credit":
            if staff_name != "Admin (Owner)" and f"({staff_name})" not in item:
                continue
            staff_credit_total += price
            for person in staff_credits.keys():
                if f"({person})" in item:
                    staff_credits[person] += price
        
    report_msg = f"No Toxic Account 🤖\n📊 **လချုပ် အစီရင်ခံစာ (Monthly Report)**\n\n"
    report_msg += "💸 [ ဆိုင်၏ အသုံးစရိတ်များ ] -\n"
    for cat in EXPENSE_CATEGORIES:
        total = cat_totals.get(cat, 0)
        report_msg += f"• {cat} = {total:,.0f}\n"
    report_msg += f"💰 **ဆိုင်၏ အသုံးစရိတ် စုစုပေါင်း = {actual_expense_total:,.0f}**\n\n"
    
    report_msg += "🍽️ [ Staff Credit (ဝန်ထမ်းအကြွေးများ) ] -\n"
    if staff_name == "Admin (Owner)":
        for person, total in staff_credits.items():
            report_msg += f"• {person} = {total:,.0f}\n"
        report_msg += f"💵 **Staff Credit စုစုပေါင်း = {staff_credit_total:,.0f}**"
    else:
        short_name = "PA PA MAY" if staff_name == "PA PA MAY" else "Sandi"
        report_msg += f"• {short_name} (မိမိအကြွေး) = {staff_credits[short_name]:,.0f}\n"
        
    bot.send_message(chat_id, report_msg)
    show_main_menu(chat_id, staff_name)

# 📝 (Detail) ခလုတ်အတွက်- ရက်သတ္တပတ်အလိုက် မက်ဆေ့ခ်ျခွဲထုတ်ပြသမည့်စနစ်
def view_monthly_detailed_report(chat_id, detail_type):
    staff_name = user_states[chat_id]["staff_name"]
    current_month_year = datetime.now().strftime("/%m/%Y")
    
    conn = sqlite3.connect('notoxic_expenses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT date, category, item_name, price, staff_name FROM store_expenses WHERE date LIKE ?", ('%' + current_month_year,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(chat_id, "📋 ယခုလအတွက် အသေးစိတ်ပြစရာ စာရင်းမရှိပါဘူးဗျာ။")
        return

    # ရက်သတ္တပတ် ၄ ခုအတွက် သီးသန့် Array များ ခွဲခြားတည်ဆောက်ခြင်း
    weeks = {
        "Week 1 (01 to 07)": [],
        "Week 2 (08 to 14)": [],
        "Week 3 (15 to 21)": [],
        "Week 4+ (22 to End)": []
    }
    
    for row in rows:
        date_str, cat, item, price, entry_staff = row
        try:
            day = int(date_str.split('/')[0])
            if 1 <= day <= 7:
                w_key = "Week 1 (01 to 07)"
            elif 8 <= day <= 14:
                w_key = "Week 2 (08 to 14)"
            elif 15 <= day <= 21:
                w_key = "Week 3 (15 to 21)"
            else:
                w_key = "Week 4+ (22 to End)"
                
            # အမျိုးအစားအလိုက် စစ်ထုတ်ခြင်း
            if detail_type == "EXPENSE" and cat in EXPENSE_CATEGORIES:
                weeks[w_key].append(f"• {date_str} - [{cat}] {item} = {price:,.0f} (by {entry_staff})")
            elif detail_type == "CREDIT" and cat == "🍽️ Staff Credit":
                # လုံခြုံရေးအရ ဝန်ထမ်းဆိုလျှင် တခြားသူစာရင်းကို လုံးဝမပြရန်
                if staff_name != "Admin (Owner)" and f"({staff_name})" not in item:
                    continue
                weeks[w_key].append(f"• {date_str} - {item} = {price:,.0f} (by {entry_staff})")
        except:
            continue

    # 📩 အပတ်စဉ်အလိုက် မက်ဆေ့ခ်ျ သီးသန့်စီ ခွဲပို့ခြင်း
    bot.send_message(chat_id, f"🤖 **No Toxic Account - [{'ဆိုင်သုံး Expense' if detail_type == 'EXPENSE' else 'Staff Credit'}] အသေးစိတ်စာရင်းချုပ်**")
    
    has_data = False
    for week_title, items in weeks.items():
        if items:
            has_data = True
            msg = f"📅 **{week_title}**\n\n" + "\n".join(items)
            bot.send_message(chat_id, msg) # 👈 တစ်ပတ်စာပြည့်တိုင်း Message တစ်စောင်စီ သီးသန့်ခွဲပို့သည်

    if not has_data:
        bot.send_message(chat_id, "📋 ၎င်းကဏ္ဍတွင် ယခုလအတွက် မည်သည့် အသေးစိတ်စာရင်းမှ မရှိသေးပါခင်ဗျာ။")
        
    show_main_menu(chat_id, staff_name)

print("Weekly Detailed & Separated system is successfully active.")
bot.polling()