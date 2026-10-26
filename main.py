import os
import random
import string
import time
import requests
import threading
from flask import Flask
from telebot import TeleBot, types

# --- [ سيرفر Keep-Alive لضمان استمرار العمل على Render ] ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Shadow Hunter Operational 24/7."

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- [ إعدادات البوت ] ---
TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

# قاموس لتتبع حالة الصيد لكل مستخدم
active_hunts = {}

def generate_username(platform):
    chars = string.ascii_lowercase + string.digits
    if platform in ["snapchat", "tiktok", "instagram", "discord"]:
        return ''.join(random.choices(chars, k=4))
    elif platform == "sony":
        base = random.choices(chars, k=4)
        special = random.choice(['-', '_'])
        pos = random.randint(1, 3)
        base.insert(pos, special)
        return ''.join(base)
    return None

def check_availability(platform, username):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        if platform == "snapchat":
            url = f"https://accounts.snapchat.com/accounts/get_username_availability?requested_username={username}"
            resp = requests.post(url, headers=headers, timeout=5)
            return resp.json().get("error_code") == "0"
        elif platform == "tiktok":
            url = f"https://www.tiktok.com/@{username}"
            resp = requests.get(url, headers=headers, timeout=5)
            return resp.status_code == 404
        elif platform == "sony":
            url = f"https://psnprofiles.com/{username}"
            resp = requests.get(url, headers=headers, timeout=5)
            return resp.status_code == 404
        elif platform == "instagram":
            url = f"https://www.instagram.com/{username}/"
            resp = requests.get(url, headers=headers, timeout=5)
            return resp.status_code == 404
        elif platform == "discord":
            url = f"https://discord.com/api/v9/users/{username}"
            resp = requests.get(url, headers=headers, timeout=5)
            return resp.status_code == 404
    except:
        return False
    return False

def hunting_worker(chat_id, user_id, platform):
    bot.send_message(chat_id, f"🎯 **تم بدء رادار الصيد للمنصة: {platform.upper()}**\nأنا أبحث الآن في الخلفية...", parse_mode="Markdown")
    
    while active_hunts.get(user_id, False):
        username = generate_username(platform)
        if check_availability(platform, username):
            bot.send_message(
                chat_id, 
                f"🔥 **تم صيد يوزر متاح بنجاح!**\n\n🌐 المنصة: `{platform.upper()}`\n👤 اليوزر: `{username}`", 
                parse_mode="Markdown"
            )
        # سرعة فحص آمنة ومتوازنة لتجنب الحظر
        time.sleep(random.uniform(1.5, 2.5))

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👻 سناب شات (رباعي)", callback_data="snapchat"),
        types.InlineKeyboardButton("🎵 تيك توك (رباعي)", callback_data="tiktok"),
        types.InlineKeyboardButton("🎮 سوني PSN (خماسي مع شخطة)", callback_data="sony"),
        types.InlineKeyboardButton("📸 إنستغرام (رباعي)", callback_data="instagram"),
        types.InlineKeyboardButton("💬 ديسكورد (رباعي)", callback_data="discord"),
        types.InlineKeyboardButton("🛑 إيقاف الصيد", callback_data="stop")
    )
    bot.send_message(message.chat.id, "🛡️ **أهلاً بك يا سيد الظل. لوحة تحكم الصيد جاهزة:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "stop":
        if active_hunts.get(user_id, False):
            active_hunts[user_id] = False
            bot.answer_callback_query(call.id, "🛑 تم إيقاف الصيد.")
            bot.send_message(chat_id, "🛑 **تم إيقاف عملية الصيد بنجاح.**", parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ لا توجد عملية صيد نشطة.", show_alert=True)
        return

    platform = call.data
    
    # إذا كانت هناك عملية قديمة تعمل، توقفها أولاً
    active_hunts[user_id] = False
    time.sleep(0.5)
    
    # بدء عملية جديدة في خيط خلفي (Background Thread)
    active_hunts[user_id] = True
    t = threading.Thread(target=hunting_worker, args=(chat_id, user_id, platform))
    t.daemon = True
    t.start()
    
    bot.answer_callback_query(call.id, f"بدء صيد {platform.upper()}...")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
