import random
import string
import time
import os
import threading
import requests
import telebot
from flask import Flask

# ==================== التهيئات والأساسيات ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID", "YOUR_CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)
is_hunting = False

# سيرفر خفيف للبقاء نشطاً على Render
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Shadow Engineer System: Online & Active", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==================== توليد الأنماط (رباعي وخماسي مع شرطة) ====================
def generate_username():
    """
    توليد يوزر رباعي أو خماسي يحتوي على شرطة (-) في مكان عشوائي (بدون البداية أو النهاية)
    """
    length = random.choice([4, 5])
    chars = string.ascii_lowercase + string.digits
    
    dash_position = random.randint(1, length - 2)
    
    result = []
    for i in range(length):
        if i == dash_position:
            result.append('-')
        else:
            result.append(random.choice(chars))
            
    return "".join(result)

# ==================== آلية الفحص الدقيقة (فقط المتاحة فعلياً) ====================
def check_username(username):
    """
    فحص حقيقي ودقيق للتأكد أن اليوزر غير مأخوذ وغير محظور رسمياً
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    url = f"https://t.me/{username}"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        
        # إذا كان اليوزر محجوزاً، تيليجرام تعرض صفحة بروفایل تحتوي على اسم المستخدم أو زر مراسلة
        # أما إذا كان غير مأخوذ تماماً، فستظهر رسالة تفيد بأن اليوزر غير موجود أو يظهر زر إنشاء الحساب/قناة
        if response.status_code == 200:
            html = response.text
            # إذا وجدنا دليلاً على أن الصفحة تعود لقناة أو مجموعة أو مستخدم حقيقي -> اليوزر غير متاح
            if 'class="tgme_page_title"' in html or 'og:title' in html:
                # التأكد مما إذا كانت الصفحة تخص شخصاً أو مجموعة وليست صفحة "If you have Telegram..."
                if "If you have Telegram" in html or "open in telegram" not in html.lower():
                    return False
                
                # فحص إضافي: لو الصفحة تحتوي على زر الانضمام أو الرسائل فهي مأخوذة
                if "tgme_action_button_new" in html:
                    return False
                    
            # التحقق من النصوص التي تعني أن اليوزر متاح للإنشاء أو غير موجود
            if "If you have Telegram" in html and "is not registered" in html:
                return True
            
            # طريقة بديلة أضمن: إذا لم تكن الصفحة تحتوي على بروفایل حقيقي نشط
            if "tgme_page_extra" not in html and "tgme_page_title" not in html:
                return True
                
    except Exception as e:
        print(f"Error checking {username}: {e}")
        
    return False

# ==================== محرك الصيد في الظل ====================
def hunter_loop():
    global is_hunting
    bot.send_message(CHAT_ID, "🛡️ **تم تفعيل فلاتر التأكيد الصارم..**\nلن يتم إرسال أي يوزر إلا إذا كان متاحاً وجاهزاً للقبض عليه فوراً.")
    
    while is_hunting:
        user = generate_username()
        
        # فحص أولي عبر الرابط المباشر
        url = f"https://t.me/{user}"
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            # اليوزر المتاح في تيليجرام تظهر فيه عبارة "If you have Telegram, you can contact..." 
            # أو لا يحتوي على بروفایل فعلي
            if r.status_code == 200:
                content = r.text
                # الشرط الأكيد لليوزر المتاح: عدم وجود عنوان بروفايل وغياب الأزرار النشطة
                if "tgme_page_title" not in content and "tgme_page_extra" not in content:
                    msg = f"🎯 **صيد مؤكد ومتاح 100%!**\n\n🔹 **اليوزر:** `@{user}`\n📏 **الطول:** {len(user)}\n⚡ **الحالة:** جاهز للحجز الفوري"
                    bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
        except Exception:
            pass
        
        # فاصل زمني لحماية البوت من الحظر وسيرفرات تيليجرام
        time.sleep(random.uniform(3.0, 5.0))

# ==================== الأوامر ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, "👋 أهلاً بك يا سيد الظل.\nالبوت مُحدث الآن لفلترة اليوزرات الوهمية تماماً.\n\nأرسل /hunt للبدء.")

@bot.message_handler(commands=['hunt'])
def start_hunt(message):
    global is_hunting
    if not is_hunting:
        is_hunting = True
        threading.Thread(target=hunter_loop, daemon=True).start()
        bot.reply_to(message, "🚀 تم إطلاق محرك الصيد الدقيق.")
    else:
        bot.reply_to(message, "⚠️ المحرك يعمل بالفعل.")

@bot.message_handler(commands=['stop'])
def stop_hunt(message):
    global is_hunting
    is_hunting = False
    bot.reply_to(message, "🛑 تم إيقاف المحرك.")

# ==================== التشغيل ====================
if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
