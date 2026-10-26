import random
import string
import time
import os
import asyncio
from flask import Flask
from telethon import TelegramClient, functions, types
from telethon.errors import FloodWaitError, UsernameOccupiedError, UsernameInvalidError

# ==================== التهيئات والأساسيات ====================
API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH"))
PHONE_NUMBER = os.environ.get("PHONE_NUMBER", "YOUR_PHONE_NUMBER")
CHAT_ID = int(os.environ.get("CHAT_ID", "YOUR_CHAT_ID")) # الحساب الذي ستصل إليه اليوزرات المتاحة

# استخدام جلسة تخزين مؤقتة للـ Userbot
client = TelegramClient('shadow_session', API_ID, API_HASH)

is_hunting = False

# سيرفر خفيف للبقاء نشطاً على Render
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Shadow Userbot System: Online & Active", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==================== توليد الأنماط (رباعي وخماسي مع شرطة) ====================
def generate_username():
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

# ==================== الفحص الحقيقي عبر فحص توفر اليوزر في النظام ====================
async def check_and_hunt():
    global is_hunting
    await client.send_message(CHAT_ID, "⚔️ **تم تفعيل اليوزربوت الخفي بنجاح!**\nجارٍ فحص اليوزرات بالطريقة الحقيقية المباشرة...")
    
    while is_hunting:
        username = generate_username()
        try:
            # محاولة التحقق من اليوزر عبر فحص إنشاء أو تحديث قناة/مجموعة باليوزر أو التحقق من توفره
            # الطريقة الأضمن والأقوى برمجياً في تليجرام للتأكد من إمكانية استخدام اليوزر:
            result = await client(functions.account.CheckUsernameRequest(
                username=username
            ))
            
            # إذا كان النتيجة True، فهذا يعني أن اليوزر متاح 100% ويمكن حجزه فوراً!
            if result:
                msg = f"🎯 **صيد مؤكد ومتاح رسميًا!**\n\n🔹 **اليوزر:** `@{username}`\n📏 **الطول:** {len(username)}\n⚡ **الحالة:** متاح وجاهز للقبض عليه"
                await client.send_message(CHAT_ID, msg)
                print(f"[SUCCESS] Available username found: @{username}")
                
        except UsernameOccupiedError:
            # اليوزر مأخوذ (خطأ طبيعي أثناء البحث)
            pass
        except UsernameInvalidError:
            # يوزر غير صالح بناءً على قواعد تليجرام
            pass
        except FloodWaitError as e:
            # حماية من الحظر المؤقت، الانتظار بالثواني المطلوبة من تيليجرام
            print(f"Flood wait: sleeping for {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"Error checking {username}: {e}")
            
        # فاصل زمني أمني لتجنب الضغط العالي
        await asyncio.sleep(3)

# ==================== تشغيل النظام ====================
async def main_loop():
    await client.start(phone=PHONE_NUMBER)
    print("Userbot is running and connected!")
    
    # أوامر التحكم البسيطة عبر رسائل الحساب نفسه أو رسائل محفوظة
    @client.on(events.NewMessage(pattern='/hunt'))
    async def start_handler(event):
        global is_hunting
        if event.sender_id == CHAT_ID:
            if not is_hunting:
                is_hunting = True
                asyncio.create_task(check_and_hunt())
                await event.respond("🚀 تم بدء عملية الصيد الحقيقية.")
            else:
                await event.respond("⚠️ الصيد يعمل بالفعل.")

    @client.on(events.NewMessage(pattern='/stop'))
    async def stop_handler(event):
        global is_hunting
        if event.sender_id == CHAT_ID:
            is_hunting = False
            await event.respond("🛑 تم إيقاف عملية الصيد.")

    await client.run_until_disconnected()

if __name__ == "__main__":
    from telethon import events
    # تشغيل سيرفر الويب بجانب اليوزربوت لضمان استمرار البقاء على Render
    import threading
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # تشغيل حلقة العمل الأساسية
    with client:
        client.loop.run_until_complete(main_loop())
