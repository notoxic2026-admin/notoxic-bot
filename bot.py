import telebot
import psycopg2
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta
import calendar

# --- Configuration ---
TOKEN = '8780973280:AAEbgwiKGCZacarCDzDjH2Wq4s4MAt_1IwU'
DATABASE_URL = 'postgresql://postgres:GyXjLVNoHouChUTuyQCvCnpTJPsQqKxM@postgres.railway.internal:5432/railway'

bot = telebot.TeleBot(TOKEN)

# --- Data & Variables ---
STAFF_PASSWORDS = {"9999": "Admin (Owner)", "1234": "PA PA MAY", "1235": "Sandi"}
BURMESE_DIGITS = {'၀': '0', '၁': '1', '၂': '2', '၃': '3', '၄': '4', '၅': '5', '၆': '6', '၇': '7', '၈': '8', '၉': '9'}
EXPENSE_CATEGORIES = ["🍻 Drinks and Cigarettes", "🍔 Food", "📢 Marketing", "📅 Fix Monthly", "🧹 Generals"]
user_states = {} 

# --- Helper Functions ---
def convert_burmese_to_english_digits(text):
    for myanmar_digit, english_digit in BURMESE_DIGITS.items():
        text = text.replace(myanmar_digit, english_digit)
    return text

def parse_date(date_text):
    clean_text = convert_burmese_to_english_digits(date_text.strip())
    clean_text = clean_text.replace('/', '-').replace('_', '-')
    try:
        parsed_date = datetime.strptime(clean_text, "%d-%m-%Y")
        return parsed_date.strftime("%Y-%m-%d"), parsed_date.strftime("%d-%m-%Y")
    except ValueError:
        return None, None

def get_main_menu(staff_name):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("💸 စာရင်းအသစ် သွင်းမည်"), KeyboardButton("📊 အစီရင်ခံစာ ကြည့်မည်"))
    if staff_name == "Admin (Owner)":
        markup.add(KeyboardButton("✏️ ပြင်မည် / ဖျက်မည် (Admin သီးသန့်)"))
    markup.add(KeyboardButton("🔄 အကောင့်ပြောင်းမည်"))
    return markup

# အပိုင်းခွဲပို့သော Function (Telegram 4000 limit အတွက်)
def send_long_message(chat_id, text):
    max_length = 3800
    while len(text) > 0:
        if len(text) <= max_length:
            bot.send_message(chat_id, text, parse_mode='Markdown')
            break
        split_index = text.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = max_length
        bot.send_message(chat_id, text[:split_index], parse_mode='Markdown')
        text = text[split_index:].strip()

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

# ==========================================
# 1. Start & Login
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 မင်္ဂလာပါ။ စာရင်းသွင်းစနစ်မှ ကြိုဆိုပါတယ်။\nကျေးဇူးပြု၍ သင့်ရဲ့ လျှို့ဝှက်နံပါတ် (Password) ကို ရိုက်ထည့်ပါ။")
    bot.register_next_step_handler(message, check_password)

def check_password(message):
    chat_id = message.chat.id
    password = convert_burmese_to_english_digits(message.text.strip())
    
    if password in STAFF_PASSWORDS:
        staff_name = STAFF_PASSWORDS[password]
        user_states[chat_id] = {"staff_name": staff_name, "draft_items": []}
        bot.send_message(chat_id, f"✅ မှန်ကန်ပါတယ်။ {staff_name} အဖြစ် ဝင်ရောက်ပြီးပါပြီ။")
        show_main_menu(chat_id)
    else:
        msg = bot.send_message(chat_id, "❌ Password မှားနေပါတယ်။ ပြန်လည်ရိုက်ထည့်ပါ။")
        bot.register_next_step_handler(msg, check_password)

def show_main_menu(chat_id):
    staff_name = user_states[chat_id].get("staff_name", "")
    markup = get_main_menu(staff_name)
    msg = bot.send_message(chat_id, "👇 အောက်ပါ လုပ်ဆောင်ချက်ကို ရွေးချယ်ပါ -", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_main_menu)

def handle_main_menu(message):
    chat_id = message.chat.id
    text = message.text
    
    if text == "💸 စာရင်းအသစ် သွင်းမည်":
        user_states[chat_id]["action"] = "add"
        ask_for_date(chat_id)
    elif text == "📊 အစီရင်ခံစာ ကြည့်မည်":
        user_states[chat_id]["action"] = "view"
        ask_report_period(chat_id)
    elif text == "✏️ ပြင်မည် / ဖျက်မည် (Admin သီးသန့်)":
        if user_states[chat_id].get("staff_name") == "Admin (Owner)":
            user_states[chat_id]["action"] = "admin_edit"
            ask_for_date(chat_id)
        else:
            show_main_menu(chat_id)
    elif text == "🔄 အကောင့်ပြောင်းမည်":
        user_states[chat_id] = {} 
        markup = telebot.types.ReplyKeyboardRemove()
        msg = bot.send_message(chat_id, "👋 အကောင့်မှ ထွက်လိုက်ပါပြီ။\nကျေးဇူးပြု၍ ဝင်ရောက်လိုသော လျှို့ဝှက်နံပါတ် (Password) အသစ်ကို ရိုက်ထည့်ပါ။", reply_markup=markup)
        bot.register_next_step_handler(msg, check_password)
    else:
        show_main_menu(chat_id)

# ==========================================
# 2. Date Selection
# ==========================================
def ask_for_date(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    today = datetime.now().strftime("%d-%m-%Y")
    yesterday = (datetime.now() - timedelta(1)).strftime("%d-%m-%Y")
    
    markup.add(KeyboardButton(today), KeyboardButton(yesterday))
    markup.add(KeyboardButton("📅 အခြားနေ့ရက် ရိုက်ထည့်မည်"))
    markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
    
    msg = bot.send_message(chat_id, "📅 နေ့စွဲကို ရွေးချယ်ပါ (သို့) ရိုက်ထည့်ပါ -", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_date_selection)

def handle_date_selection(message):
    chat_id = message.chat.id
    text = message.text
    if text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
    if text == "📅 အခြားနေ့ရက် ရိုက်ထည့်မည်":
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
        msg = bot.send_message(chat_id, "📅 လိုချင်သော နေ့စွဲကို ရိုက်ထည့်ပါ\nပုံစံ: DD-MM-YYYY (သို့) DD_MM_YYYY", reply_markup=markup)
        bot.register_next_step_handler(msg, process_custom_date)
        return

    db_date, display_date = parse_date(text)
    if db_date:
        user_states[chat_id]["db_date"] = db_date
        user_states[chat_id]["display_date"] = display_date
        if user_states[chat_id].get("action") == "add":
            show_category_menu(chat_id)
        else:
            show_admin_db_items(chat_id)
    else:
        msg = bot.send_message(chat_id, "❌ နေ့စွဲပုံစံ မှားနေပါသည်။ ပြန်လည်ရွေးချယ်ပါ။")
        bot.register_next_step_handler(msg, handle_date_selection)

def process_custom_date(message):
    chat_id = message.chat.id
    if message.text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
    db_date, display_date = parse_date(message.text)
    if db_date:
        user_states[chat_id]["db_date"] = db_date
        user_states[chat_id]["display_date"] = display_date
        if user_states[chat_id].get("action") == "add":
            show_category_menu(chat_id)
        else:
            show_admin_db_items(chat_id)
    else:
        msg = bot.send_message(chat_id, "❌ နေ့စွဲပုံစံ မှားနေပါသည်။ ပြန်လည်ရိုက်ထည့်ပါ။")
        bot.register_next_step_handler(msg, process_custom_date)

# ==========================================
# 3. Add Expense & Draft System (With Advanced Format)
# ==========================================
def show_category_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in EXPENSE_CATEGORIES:
        markup.add(KeyboardButton(cat))
    markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
    msg = bot.send_message(chat_id, "📂 ကုန်ကျစရိတ် အမျိုးအစား ရွေးပါ -", reply_markup=markup)
    bot.register_next_step_handler(msg, start_drafting)

def start_drafting(message):
    chat_id = message.chat.id
    if message.text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
    user_states[chat_id]["category"] = message.text
    user_states[chat_id]["draft_items"] = []
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("✅ အားလုံးသိမ်းမည် (Save)"))
    markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
    
    guide_msg = (
        "📝 စာရင်းများကို တစ်ခုချင်းစီ (သို့) အများကြီး ရိုက်ထည့်နိုင်ပါပြီ။\n\n"
        "💡 **ပုံစံ (၁):** ပစ္စည်း * အရေအတွက် = စုစုပေါင်းစျေး (ဥပမာ - `Egg*2=100`)\n"
        "💡 **ပုံစံ (၂):** ပစ္စည်း x အရေအတွက် = စုစုပေါင်းစျေး (ဥပမာ - `Beer x 3 = 300`)\n"
        "💡 **ပုံစံ (၃):** ရိုးရိုးပစ္စည်း = စျေးနှုန်း (ဥပမာ - `Ice=50` ဟုရိုက်ပါက အရေအတွက်ကို 1 ဟု ယူဆပါမည်)\n\n"
        "💡 *ပြီးပါက အောက်ရှိ **[✅ အားလုံးသိမ်းမည် (Save)]** ကို နှိပ်ပါ။*"
    )
    msg = bot.send_message(chat_id, guide_msg, reply_markup=markup, parse_mode='Markdown')
    bot.register_next_step_handler(msg, handle_draft_input)

def handle_draft_input(message):
    chat_id = message.chat.id
    text = message.text.strip()
    if text == "❌ ပယ်ဖျက်မည်":
        user_states[chat_id]["draft_items"] = []
        show_main_menu(chat_id)
        return
    if text == "✅ အားလုံးသိမ်းမည် (Save)":
        save_draft_to_db(chat_id)
        return
    if text == "✏️ မသိမ်းခင် ပြန်ပြင်မည် / ဖျက်မည်":
        show_draft_edit_menu(chat_id)
        return

    raw_text = convert_burmese_to_english_digits(text)
    lines = raw_text.split('\n')
    added_count = 0
    reply_text = ""
    
    for line in lines:
        if '=' in line:
            parts = line.split('=')
            left_side = parts[0].strip()
            try:
                price = float(parts[1].strip())
                
                # အမြှောက်စနစ် (*) သို့မဟုတ် (x) ပါမပါ စစ်ဆေးခြင်း
                if '*' in left_side:
                    sub_parts = left_side.split('*')
                    item_name = f"{sub_parts[0].strip()} ({sub_parts[1].strip()} ခု)"
                elif 'x' in left_side:
                    sub_parts = left_side.split('x')
                    item_name = f"{sub_parts[0].strip()} ({sub_parts[1].strip()} ခု)"
                elif 'X' in left_side:
                    sub_parts = left_side.split('X')
                    item_name = f"{sub_parts[0].strip()} ({sub_parts[1].strip()} ခု)"
                else:
                    item_name = f"{left_side} (1 ခု)" # မပါရင် 1 ဟုအလိုအလျောက်ယူဆ
                    
                user_states[chat_id]["draft_items"].append({"name": item_name, "price": price})
                added_count += 1
                reply_text += f"• {item_name} = {price:g} Ks\n"
            except (ValueError, IndexError):
                pass
                
    if added_count > 0:
        total_drafts = len(user_states[chat_id]["draft_items"])
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("✅ အားလုံးသိမ်းမည် (Save)"))
        markup.add(KeyboardButton("✏️ မသိမ်းခင် ပြန်ပြင်မည် / ဖျက်မည်"))
        markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
        bot.send_message(chat_id, f"➕ **မှတ်သားထားပါသည်:**\n{reply_text}\n*(လက်ရှိ ယာယီစာရင်း: {total_drafts} ခု)*", reply_markup=markup, parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "❌ ပုံစံမှားနေပါသည်။ (ဥပမာ - Egg*2=100 သို့မဟုတ် Ice=50) ဟု ရိုက်ထည့်ပါ။")
    bot.register_next_step_handler(message, handle_draft_input)

def show_draft_edit_menu(chat_id):
    drafts = user_states[chat_id].get("draft_items", [])
    if not drafts:
        msg = bot.send_message(chat_id, "ယာယီစာရင်း မရှိသေးပါ။ စာရင်းဆက်သွင်းပါ။")
        bot.register_next_step_handler(msg, handle_draft_input)
        return
    reply = "📝 **လက်ရှိ ယာယီစာရင်းများ**\n\n"
    for idx, item in enumerate(drafts):
        reply += f"[{idx+1}] {item['name']} = {item['price']:g} Ks\n"
    reply += "\n✏️ ပြင်/ဖျက် လိုသော စာရင်း၏ **နံပါတ်စဉ်** ကို ရိုက်ထည့်ပါ (ဥပမာ - 1):"
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("❌ နောက်ဆုတ်မည်"))
    msg = bot.send_message(chat_id, reply, reply_markup=markup, parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_draft_edit_choice)

def process_draft_edit_choice(message):
    chat_id = message.chat.id
    if message.text == "❌ နောက်ဆုတ်မည်":
        msg = bot.send_message(chat_id, "စာရင်းဆက်သွင်းပါ။ (သို့) Save နှိပ်ပါ။")
        bot.register_next_step_handler(msg, handle_draft_input)
        return
    try:
        idx = int(convert_burmese_to_english_digits(message.text)) - 1
        drafts = user_states[chat_id]["draft_items"]
        if 0 <= idx < len(drafts):
            user_states[chat_id]["edit_draft_idx"] = idx
            target = drafts[idx]
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton("✏️ အသစ်ပြန်ပြင်ရေးမည်"), KeyboardButton("🗑️ ယာယီစာရင်းမှ ဖျက်မည်"))
            markup.add(KeyboardButton("❌ နောက်ဆုတ်မည်"))
            msg = bot.send_message(chat_id, f"📌 ရွေးချယ်ထားသော စာရင်း: **[{target['name']} = {target['price']:g} Ks]**", reply_markup=markup, parse_mode='Markdown')
            bot.register_next_step_handler(msg, execute_draft_action)
        else:
            msg = bot.send_message(chat_id, "❌ နံပါတ်စဉ် မှားနေပါသည်။")
            bot.register_next_step_handler(msg, process_draft_edit_choice)
    except ValueError:
        msg = bot.send_message(chat_id, "❌ ဂဏန်းသာ ရိုက်ထည့်ပါ။")
        bot.register_next_step_handler(msg, process_draft_edit_choice)

def execute_draft_action(message):
    chat_id = message.chat.id
    action = message.text
    idx = user_states[chat_id].get("edit_draft_idx")
    if action == "❌ နောက်ဆုတ်မည်":
        show_draft_edit_menu(chat_id)
        return
    if action == "🗑️ ယာယီစာရင်းမှ ဖျက်မည်":
        deleted = user_states[chat_id]["draft_items"].pop(idx)
        bot.send_message(chat_id, f"✅ [{deleted['name']}] ကို ဖျက်လိုက်ပါပြီ။")
        show_draft_edit_menu(chat_id)
    elif action == "✏️ အသစ်ပြန်ပြင်ရေးမည်":
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("❌ နောက်ဆုတ်မည်"))
        msg = bot.send_message(chat_id, "📝 စာရင်းအသစ်ကို ပုံစံအတိုင်း ပြန်လည်ရိုက်ထည့်ပါ။\n(ဥပမာ - Egg*2=100 သို့မဟုတ် Ice=50)", reply_markup=markup)
        bot.register_next_step_handler(msg, save_edited_draft)

def save_edited_draft(message):
    chat_id = message.chat.id
    if message.text == "❌ နောက်ဆုတ်မည်":
        show_draft_edit_menu(chat_id)
        return
    text = convert_burmese_to_english_digits(message.text)
    if '=' in text:
        parts = text.split('=')
        left_side = parts[0].strip()
        try:
            price = float(parts[1].strip())
            if '*' in left_side:
                sub_parts = left_side.split('*')
                item_name = f"{sub_parts[0].strip()} ({sub_parts[1].strip()} ခု)"
            elif 'x' in left_side:
                sub_parts = left_side.split('x')
                item_name = f"{sub_parts[0].strip()} ({sub_parts[1].strip()} ခု)"
            elif 'X' in left_side:
                sub_parts = left_side.split('X')
                item_name = f"{sub_parts[0].strip()} ({sub_parts[1].strip()} ခု)"
            else:
                item_name = f"{left_side} (1 ခု)"
                
            idx = user_states[chat_id]["edit_draft_idx"]
            user_states[chat_id]["draft_items"][idx] = {"name": item_name, "price": price}
            bot.send_message(chat_id, "✅ အောင်မြင်စွာ ပြင်ဆင်ပြီးပါပြီ။")
            show_draft_edit_menu(chat_id)
        except (ValueError, IndexError):
            msg = bot.send_message(chat_id, "❌ စျေးနှုန်းမှားနေပါသည်။ ပြန်ရိုက်ပါ။")
            bot.register_next_step_handler(msg, save_edited_draft)
    else:
        msg = bot.send_message(chat_id, "❌ ပုံစံမှားနေပါသည်။ ပြန်ရိုက်ပါ။")
        bot.register_next_step_handler(msg, save_edited_draft)

def save_draft_to_db(chat_id):
    drafts = user_states[chat_id].get("draft_items", [])
    if not drafts:
        bot.send_message(chat_id, "❌ သိမ်းဆည်းရန် စာရင်းမရှိပါ။")
        show_main_menu(chat_id)
        return
    staff = user_states[chat_id]["staff_name"]
    db_date = user_states[chat_id]["db_date"]
    display_date = user_states[chat_id]["display_date"]
    category = user_states[chat_id]["category"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    saved_text = ""
    total = 0
    for idx, item in enumerate(drafts):
        cursor.execute('INSERT INTO store_expenses (date, staff_name, category, item_name, price) VALUES (%s, %s, %s, %s, %s)', (db_date, staff, category, item["name"], item["price"]))
        saved_text += f"{idx+1}. {item['name']} = {item['price']:g} Ks\n"
        total += item['price']
        
    conn.commit()
    conn.close()
    user_states[chat_id]["draft_items"] = []
    
    reply = f"✅ **{display_date}** ရက်စွဲပါ **{category}** အတွက် Database သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ:\n\n{saved_text}\n💰 **စုစုပေါင်း = {total:g} Ks**"
    bot.send_message(chat_id, reply, parse_mode='Markdown')
    show_main_menu(chat_id)

# ==========================================
# 4. Advanced Report System (Total & Detail)
# ==========================================
def ask_report_period(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📅 ဒီနေ့"), KeyboardButton("📅 မနေ့က"))
    markup.add(KeyboardButton("🗓️ ဒီတစ်ပတ်စာ (Weekly)"), KeyboardButton("🗓️ ဒီတစ်လစာ (Monthly)"))
    markup.add(KeyboardButton("📅 သတ်မှတ်ရက်စွဲ (Custom)"))
    markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
    
    msg = bot.send_message(chat_id, "📅 ဘယ်အချိန်အတွက် အစီရင်ခံစာ ကြည့်ချင်ပါသလဲ?", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_report_period)

def handle_report_period(message):
    chat_id = message.chat.id
    text = message.text
    
    today = datetime.now()
    start_date = ""
    end_date = ""
    title = ""

    if text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
    elif text == "📅 ဒီနေ့":
        start_date = end_date = today.strftime("%Y-%m-%d")
        title = today.strftime("%d-%m-%Y")
    elif text == "📅 မနေ့က":
        yesterday = today - timedelta(1)
        start_date = end_date = yesterday.strftime("%Y-%m-%d")
        title = yesterday.strftime("%d-%m-%Y")
    elif text == "🗓️ ဒီတစ်ပတ်စာ (Weekly)":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        start_date = start.strftime("%Y-%m-%d")
        end_date = end.strftime("%Y-%m-%d")
        title = "ဒီတစ်ပတ်စာ"
    elif text == "🗓️ ဒီတစ်လစာ (Monthly)":
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day).strftime("%Y-%m-%d")
        title = "ဒီတစ်လစာ"
    elif text == "📅 သတ်မှတ်ရက်စွဲ (Custom)":
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
        msg = bot.send_message(chat_id, "📅 ရက်စွဲကို ရိုက်ထည့်ပါ။ (ဥပမာ: 25-05-2026)", reply_markup=markup)
        bot.register_next_step_handler(msg, process_custom_report_date)
        return
    else:
        ask_report_period(chat_id)
        return

    user_states[chat_id]["rep_start"] = start_date
    user_states[chat_id]["rep_end"] = end_date
    user_states[chat_id]["rep_title"] = title
    ask_report_type(chat_id)

def process_custom_report_date(message):
    chat_id = message.chat.id
    if message.text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
    db_date, display_date = parse_date(message.text)
    if db_date:
        user_states[chat_id]["rep_start"] = db_date
        user_states[chat_id]["rep_end"] = db_date
        user_states[chat_id]["rep_title"] = display_date
        ask_report_type(chat_id)
    else:
        msg = bot.send_message(chat_id, "❌ နေ့စွဲပုံစံ မှားနေပါသည်။ ပြန်လည်ရိုက်ထည့်ပါ။")
        bot.register_next_step_handler(msg, process_custom_report_date)

def ask_report_type(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📊 အကျဉ်းချုပ်သာ ကြည့်မည် (Total)"))
    markup.add(KeyboardButton("📝 အသေးစိတ် ကြည့်မည် (Detail)"))
    markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
    msg = bot.send_message(chat_id, "📊 Report ကို ဘယ်လိုပုံစံ ကြည့်ချင်ပါသလဲ?", reply_markup=markup)
    bot.register_next_step_handler(msg, generate_report)

def generate_report(message):
    chat_id = message.chat.id
    text = message.text
    if text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
        
    start_date = user_states[chat_id]["rep_start"]
    end_date = user_states[chat_id]["rep_end"]
    title = user_states[chat_id]["rep_title"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if text == "📊 အကျဉ်းချုပ်သာ ကြည့်မည် (Total)":
        cursor.execute("SELECT category, SUM(price) FROM store_expenses WHERE date BETWEEN %s AND %s GROUP BY category ORDER BY category", (start_date, end_date))
        rows = cursor.fetchall()
        
        if not rows:
            bot.send_message(chat_id, f"📅 {title} အတွက် စာရင်း မရှိသေးပါ။")
        else:
            report = f"📊 **{title} အကျဉ်းချုပ် အစီရင်ခံစာ**\n━━━━━━━━━━━━━━━━━━━\n"
            total = 0
            for row in rows:
                report += f"**{row[0]}** = {row[1]:g} Ks\n"
                total += row[1]
            report += f"━━━━━━━━━━━━━━━━━━━\n💰 **စုစုပေါင်း = {total:g} Ks**"
            bot.send_message(chat_id, report, parse_mode='Markdown')
            
    elif text == "📝 အသေးစိတ် ကြည့်မည် (Detail)":
        cursor.execute("SELECT date, category, item_name, price, staff_name FROM store_expenses WHERE date BETWEEN %s AND %s ORDER BY category, date", (start_date, end_date))
        rows = cursor.fetchall()
        
        if not rows:
            bot.send_message(chat_id, f"📅 {title} အတွက် စာရင်း မရှိသေးပါ။")
        else:
            report = f"📝 **{title} အသေးစိတ် အစီရင်ခံစာ**\n━━━━━━━━━━━━━━━━━━━\n"
            total = 0
            current_category = ""
            
            for row in rows:
                r_date, category, item, price, staff = row
                display_d = datetime.strptime(r_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                if category != current_category:
                    report += f"\n**{category}**\n"
                    current_category = category
                
                report += f"• {display_d}: {item} = {price:g} Ks ({staff})\n"
                total += price
                
            report += f"━━━━━━━━━━━━━━━━━━━\n💰 **စုစုပေါင်း = {total:g} Ks**"
            send_long_message(chat_id, report)
            
    conn.close()
    show_main_menu(chat_id)

# ==========================================
# 5. Admin Edit / Delete (DB Level)
# ==========================================
def show_admin_db_items(chat_id):
    db_date = user_states[chat_id]["db_date"]
    display_date = user_states[chat_id]["display_date"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, item_name, price, staff_name FROM store_expenses WHERE date = %s ORDER BY id", (db_date,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(chat_id, f"📅 {display_date} တွင် ပြင်ဆင်ရန် စာရင်း မရှိပါ။")
        show_main_menu(chat_id)
        return
        
    reply = f"📂 **{display_date} ၏ စာရင်းများ**\n\n"
    for row in rows:
        reply += f"[ID: {row[0]}] {row[2]} = {row[3]:g} Ks ({row[1]})\n"
    reply += "\n✏️ ပြင်/ဖျက် လိုသော စာရင်း၏ **ID နံပါတ်** ကို ရိုက်ထည့်ပါ:"
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
    send_long_message(chat_id, reply) 
    bot.register_next_step_handler_by_chat_id(chat_id, process_admin_edit_choice)

def process_admin_edit_choice(message):
    chat_id = message.chat.id
    if message.text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
    try:
        db_id = int(convert_burmese_to_english_digits(message.text))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT item_name, price FROM store_expenses WHERE id = %s", (db_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user_states[chat_id]["edit_db_id"] = db_id
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(KeyboardButton("✏️ အသစ်ပြင်ရေးမည်"), KeyboardButton("🗑️ အပြီးအပိုင် ဖျက်မည်"))
            markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
            msg = bot.send_message(chat_id, f"📌 ရွေးချယ်ထားသော စာရင်း: **[{row[0]} = {row[1]:g} Ks]**\nဘာဆက်လုပ်ချင်ပါသလဲ?", reply_markup=markup, parse_mode='Markdown')
            bot.register_next_step_handler(msg, execute_admin_db_action)
        else:
            msg = bot.send_message(chat_id, "❌ ID နံပါတ် မတွေ့ရှိပါ။ ပြန်ရိုက်ထည့်ပါ။")
            bot.register_next_step_handler(msg, process_admin_edit_choice)
    except ValueError:
        msg = bot.send_message(chat_id, "❌ ID နံပါတ် (ဂဏန်း) သာ ရိုက်ထည့်ပါ။")
        bot.register_next_step_handler(msg, process_admin_edit_choice)

def execute_admin_db_action(message):
    chat_id = message.chat.id
    action = message.text
    db_id = user_states[chat_id].get("edit_db_id")
    if action == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
    if action == "🗑️ အပြီးအပိုင် ဖျက်မည်":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM store_expenses WHERE id = %s", (db_id,))
        conn.commit()
        conn.close()
        bot.send_message(chat_id, "✅ စာရင်းကို Database မှ အောင်မြင်စွာ ဖျက်သိမ်းပြီးပါပြီ။")
        show_main_menu(chat_id)
    elif action == "✏️ အသစ်ပြင်ရေးမည်":
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("❌ ပယ်ဖျက်မည်"))
        msg = bot.send_message(chat_id, "📝 စာရင်းအသစ်ကို ပုံစံအတိုင်း ပြန်လည်ရိုက်ထည့်ပါ။\n(ဥပမာ - Egg*2=100 သို့မဟုတ် Ice=50)", reply_markup=markup)
        bot.register_next_step_handler(msg, save_edited_db_item)

def save_edited_db_item(message):
    chat_id = message.chat.id
    if message.text == "❌ ပယ်ဖျက်မည်":
        show_main_menu(chat_id)
        return
    text = convert_burmese_to_english_digits(message.text)
    if '=' in text:
        parts = text.split('=')
        left_side = parts[0].strip()
        try:
            price = float(parts[1].strip())
            if '*' in left_side:
                sub_parts = left_side.split('*')
                item_name = f"{sub_parts[0].strip()} ({sub_parts[1].strip()} ခု)"
            elif 'x' in left_side:
                sub_parts = left_side.split('x')
                item_name = f"{sub_parts[0].strip()} ({sub_parts[1].strip()} ခု)"
            elif 'X' in left_side:
                sub_parts = left_side.split('X')
                item_name = f"{sub_parts[0].strip()} ({sub_parts[1].strip()} ခု)"
            else:
                item_name = f"{left_side} (1 ခု)"
                
            db_id = user_states[chat_id]["edit_db_id"]
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE store_expenses SET item_name = %s, price = %s WHERE id = %s", (item_name, price, db_id))
            conn.commit()
            conn.close()
            bot.send_message(chat_id, "✅ စာရင်းကို အောင်မြင်စွာ ပြင်ဆင်ပြီးပါပြီ။")
            show_main_menu(chat_id)
        except (ValueError, IndexError):
            msg = bot.send_message(chat_id, "❌ စျေးနှုန်းမှားနေပါသည်။ ပြန်ရိုက်ပါ။")
            bot.register_next_step_handler(msg, save_edited_db_item)
    else:
        msg = bot.send_message(chat_id, "❌ ပုံစံမှားနေပါသည်။ ပြန်ရိုက်ပါ။")
        bot.register_next_step_handler(msg, save_edited_db_item)

bot.polling(none_stop=True)
