import os
import random
import string
import asyncio
import aiohttp
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# --- [ 1. Flask Server لضمان عمل Render 24/7 ] ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Shadow Telegram Bot Operational."

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- [ 2. إعدادات بوت تيليجرام ] ---
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/605.1.15"
]

active_hunts = {}

# --- [ 3. مولدات اليوزرات ] ---
def generate_username(platform):
    chars = string.ascii_lowercase + string.digits
    if platform == "snapchat":
        return ''.join(random.choices(chars, k=4))
    elif platform == "tiktok":
        return ''.join(random.choices(chars, k=4))
    elif platform == "sony":
        # 5 خانات مع شرطة أو شخطة سفلية
        base = random.choices(chars, k=4)
        special = random.choice(['-', '_'])
        pos = random.randint(1, 3)
        base.insert(pos, special)
        return ''.join(base)
    elif platform == "instagram":
        return ''.join(random.choices(chars, k=4))
    elif platform == "discord":
        return ''.join(random.choices(chars, k=4))
    return None

# --- [ 4. محرك الفحص الرقمي ] ---
async def check_availability(session, platform, username):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        if platform == "snapchat":
            url = f"https://accounts.snapchat.com/accounts/get_username_availability?requested_username={username}"
            async with session.post(url, headers=headers, timeout=5) as resp:
                data = await resp.json()
                return data.get("error_code") == "0"
        
        elif platform == "tiktok":
            url = f"https://www.tiktok.com/@{username}"
            async with session.get(url, headers=headers, timeout=5) as resp:
                return resp.status == 404
        
        elif platform == "sony":
            url = f"https://psnprofiles.com/{username}"
            async with session.get(url, headers=headers, timeout=5) as resp:
                return resp.status == 404
        
        elif platform == "instagram":
            url = f"https://www.instagram.com/{username}/"
            async with session.get(url, headers=headers, timeout=5) as resp:
                return resp.status == 404

        elif platform == "discord":
            url = f"https://discord.com/api/v9/users/{username}"
            async with session.get(url, headers=headers, timeout=5) as resp:
                return resp.status == 404

    except Exception:
        return False
    return False

# --- [ 5. واجهات وأوامر التيليجرام ] ---
def get_platforms_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="👻 سناب شات (رباعي)", callback_data="hunt_snapchat")],
        [InlineKeyboardButton(text="🎵 تيك توك (رباعي)", callback_data="hunt_tiktok")],
        [InlineKeyboardButton(text="🎮 سوني PSN (خماسي مع شخطة)", callback_data="hunt_sony")],
        [InlineKeyboardButton(text="📸 إنستغرام (رباعي)", callback_data="hunt_instagram")],
        [InlineKeyboardButton(text="💬 ديسكورد (رباعي)", callback_data="hunt_discord")],
        [InlineKeyboardButton(text="🛑 إيقاف الصيد", callback_data="stop_hunt")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🛡️ **أهلاً بك يا سيد الظل في نظام صيد اليوزرات.**\nاختر المنصة لبدء العمليات الخفية:",
        reply_markup=get_platforms_keyboard()
    )

@dp.callback_query(F.data.startswith("hunt_"))
async def start_hunting_callback(callback: CallbackQuery):
    platform = callback.data.split("_")[1]
    user_id = callback.from_user.id

    if active_hunts.get(user_id):
        await callback.answer("⚠️ لديك عملية صيد قيد التشغيل بالفعل!", show_alert=True)
        return

    active_hunts[user_id] = True
    await callback.message.answer(f"🎯 **بدء صيد يوزرات {platform.upper()}...**\nسأقوم بتنبيهك فور العثور على يوزر متاح.")
    await callback.answer()

    async with aiohttp.ClientSession() as session:
        while active_hunts.get(user_id, False):
            username = generate_username(platform)
            is_available = await check_availability(session, platform, username)

            if is_available:
                await bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f"🔥 **تم صيد يوزر متاح!**\n\n🌐 المنصة: `{platform.upper()}`\n👤 اليوزر: `{username}`"
                )

            # معدل التأخير الآمن لمنع الحظر
            await asyncio.sleep(random.uniform(1.2, 2.2))

@dp.callback_query(F.data == "stop_hunt")
async def stop_hunting_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if active_hunts.get(user_id):
        active_hunts[user_id] = False
        del active_hunts[user_id]
        await callback.message.answer("🛑 **تم إيقاف عملية الصيد بنجاح.**")
    else:
        await callback.answer("❌ لا توجد عملية صيد نشطة.", show_alert=True)
    await callback.answer()

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
