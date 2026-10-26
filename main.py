import os
import random
import string
import asyncio
import aiohttp
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands

# --- [ 1. Flask Server لضمان عمل Render بشكل مستمر ] ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Shadow System Operational 24/7."

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- [ 2. إعدادات Discord Bot ] ---
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# نظام تدوير العناوين المتنكرة
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/605.1.15"
]

# قاموس لإدارة عمليات الصيد النشطة
active_hunts = {}

# --- [ 3. مولدات اليوزرات ] ---
def generate_username(platform):
    chars = string.ascii_lowercase + string.digits
    if platform == "snapchat":
        return ''.join(random.choices(chars, k=4))
    elif platform == "tiktok":
        return ''.join(random.choices(chars, k=4))
    elif platform == "sony":
        # 5 خانات تحتوي على - أو _
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
            # فحص خفيف لروابط الدعوة الكلاسيكية أو المعرفات
            url = f"https://discord.com/api/v9/users/{username}"
            async with session.get(url, headers=headers, timeout=5) as resp:
                return resp.status == 404

    except Exception:
        return False
    return False

# --- [ 5. أوامر ديسكورد ] ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} | Systems Nominal.")

class ControlView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.select(
        placeholder="اختر المنصة لبدء الصيد...",
        options=[
            discord.SelectOption(label="سناب شات (رباعي)", value="snapchat", emoji="👻"),
            discord.SelectOption(label="تيك توك (رباعي)", value="tiktok", emoji="🎵"),
            discord.SelectOption(label="سوني PSN (خماسي مع شحطة)", value="sony", emoji="🎮"),
            discord.SelectOption(label="إنستغرام (رباعي)", value="instagram", emoji="📸"),
            discord.SelectOption(label="ديسكورد (رباعي)", value="discord", emoji="💬"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        platform = select.values[0]
        user_id = interaction.user.id
        
        if user_id in active_hunts:
            await interaction.response.send_message("⚠️ هناك عملية صيد قائمة بالفعل! أوقفها أولاً باستخدام `/stop`.", ephemeral=True)
            return

        active_hunts[user_id] = True
        await interaction.response.send_message(f"🎯 تم تشغيل الصيد للمنصة: **{platform.upper()}**\nسأقوم بإرسال اليوزرات المتاحة فوراً...", ephemeral=False)
        
        asyncio.create_task(start_hunting(interaction.channel, user_id, platform))

async def start_hunting(channel, user_id, platform):
    async with aiohttp.ClientSession() as session:
        while active_hunts.get(user_id, False):
            username = generate_username(platform)
            is_available = await check_availability(session, platform, username)
            
            if is_available:
                embed = discord.Embed(
                    title="🔥 تم صيد يوزر متاح!",
                    color=discord.Color.green()
                )
                embed.add_field(name="المنصة", value=platform.upper(), inline=True)
                embed.add_field(name="اليوزر", value=f"`{username}`", inline=True)
                embed.set_footer(text="Shadow Systems | Ready for Claim")
                await channel.send(embed=embed)
            
            # معدل التأخير الآمن لمنع الحظر (بين 1.2 و 2.2 ثانية)
            await asyncio.sleep(random.uniform(1.2, 2.2))

@bot.command(name="hunt")
async def hunt_command(ctx):
    view = ControlView(ctx)
    await ctx.send("⚙️ **لوحة تحكم الصيد الخفية:**", view=view)

@bot.command(name="stop")
async def stop_command(ctx):
    user_id = ctx.author.id
    if user_id in active_hunts:
        active_hunts[user_id] = False
        del active_hunts[user_id]
        await ctx.send("🛑 **تم إيقاف عملية الصيد بنجاح.**")
    else:
        await ctx.send("❌ لا توجد عمليات صيد نشطة لحسابك.")

if __name__ == "__main__":
    keep_alive()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN is missing!")
