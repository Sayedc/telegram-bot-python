# main.py - البوت الفاخر مع لوحة أدمن متطورة
import os
import re
import json
import asyncio
import random
import shutil
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

from config import BOT_TOKEN, ADMIN_IDS, MAX_FILE_SIZE_MB, DOWNLOADS_PATH

# ========== إعدادات أولية ==========
os.makedirs(DOWNLOADS_PATH, exist_ok=True)
START_TIME = datetime.now()

SIGNATURE = "✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨"
VERSION = "FINAL_10.0"

# ========== المنصات الممنوعة (أغاني) ==========
BANNED_PLATFORMS = [
    'soundcloud', 'spotify', 'deezer', 'anghami', 'apple music',
    'tidal', 'amazon music', 'youtube music', 'saavn', 'jio saavn',
    'gaana', 'wynk', 'hungama', 'boomplay', 'audiomack', 'bandcamp',
    'mixcloud', 'hearthis', 'reverbnation', 'datpiff', 'spinrilla'
]

# ========== ستيكرات ثابتة عشوائية ==========
STICKERS = {
    "processing": ["🔄", "⚙️", "⏳", "⌛", "📥", "🔧", "⚡", "💨", "🚀", "🎬", "📀", "⏰", "🕒", "🔁", "🌀"],
    "success": ["🎉", "✅", "🤍", "🔥", "💎", "⭐", "🏆", "🎬", "📀", "⚡", "💫", "🌟", "🍿", "🎥", "📹"],
    "error": ["❌", "⚠️", "🚫", "💔", "😅", "🤦", "🙈", "🥲", "🔁"]
}

# ========== كاموس كبير للرسائل العشوائية ==========
PROCESSING_TEXTS = [
    "يتم التحميل يا {name} ⚡",
    "شوية صبر يا {name} 🎬",
    "على توكل على الله يا {name} 🚀",
    "استنى بس يا {name} 🤍",
    "جهز نفسك يا {name} 🔥",
    "خلصنا يا {name} تقريباً 💫",
    "البوت بيشتغل بسرعة الضوء يا {name} ⚡",
    "تحت أمرك يا {name} 🎯",
    "وريني إبداعك يا {name} 🌟",
    "نزلك الفيديو يا معلم {name} 🎬",
    "تسلم إيدك يا {name} 🤲",
    "ربنا معاك يا {name} 💪"
]

SUCCESS_TEXTS = [
    "🎬 خد الفيديو يا باشا",
    "✅ تم يا فنان",
    "🔥 ألف هنا",
    "💎 استلم وادعيلي",
    "⭐ عقبال ما تسمعه",
    "🏆 تحفة يا باشا",
    "💫 الله ينور عليك",
    "🌟 أنت ملك التحميلات",
    "🍿 جهز الفشار",
    "🎥 استلم وخلاص",
    "📀 تسلم إيدك",
    "🤍 يا فخر الشباب"
]

ERROR_TEXTS = [
    "❌ معلش الفيديو معدش موجود يا باشا",
    "⚠️ حاجة غلطت، جرب فيديو تاني",
    "🚫 المنصة دي مقفلة التحميل حالياً",
    "💔 الفيديو يمكن خاص أو اتحذف",
    "😅 حاول تاني يا كبير",
    "🔄 جرب رابط آخر",
    "🤦 مش عارف أوصله، جرب حاجة تانية",
    "🥲 للأسف فشلت المرة دي",
    "🔁 الرابط مش شغال، جرب غيره"
]

WELCOME_RESPONSES = [
    "🎬 اهلاً بيك يا باشا {name}! 🤍\n\n⚠️ *تنبيه مهم:* البوت مخصص لتحميل الفيديوهات فقط! 🚫\n❌ ممنوع تحميل الأغاني من أي منصة (SoundCloud, Spotify, إلخ)",
    "💫 نورت يا فنان {name}! 🌟\n\n🎯 *ملاحظة:* احنا بنحمّل فيديوهات بس! 📹\n🚫 أي محاولة لتحميل أغاني هتترفض فوراً",
    "🔥 يا مرحباً يا كبير {name}! 😎\n\n📌 *تنبيه:* البوت للفيديوهات فقط من يوتيوب، فيسبوك، تيك توك\n❌ مفيش أغاني خالص!"
]

BANNED_MESSAGE = f"""
🚫 *عذراً يا باشا!* 🚫

╔══════════════════════╗
║  ❌ منصة أغاني ❌     ║
╚══════════════════════╝

🎵 *البوت مخصص للفيديوهات فقط!*

✅ *المسموح:*
• TikTok 🎬
• YouTube 🎬
• Facebook 📘

❌ *الممنوع (أغاني):*
• SoundCloud 🎵
• Spotify 🎧
• Deezer 📀
• Anghami 🎶
• Apple Music 🍎

💡 جرب رابط فيديو بدلاً من كده 🤍
{SIGNATURE}
"""

def get_random_sticker(category):
    return random.choice(STICKERS.get(category, ["🎉"]))

def get_random_processing_text(name):
    return random.choice(PROCESSING_TEXTS).format(name=name)

def get_random_success_text():
    return random.choice(SUCCESS_TEXTS)

def get_random_error_text():
    return random.choice(ERROR_TEXTS)

def get_response(responses, name=None):
    text = responses[datetime.now().second % len(responses)]
    return text.format(name=name) if name else text

def is_music_platform(url):
    url_lower = url.lower()
    for platform in BANNED_PLATFORMS:
        if platform in url_lower:
            return True
    return False

# ========== قاعدة بيانات متطورة ==========
DB_FILE = "bot_database.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({
                "users": {},
                "total": 0,
                "daily": 0,
                "last_date": str(datetime.now().date())
            }, f, indent=2)

def save_user(user_id, username):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {
                "name": username,
                "first_seen": str(datetime.now()),
                "last_seen": str(datetime.now()),
                "downloads": 0,
                "fav_platform": "None",
                "platforms": {"YouTube": 0, "TikTok": 0, "Facebook": 0},
                "blocked": False
            }
            f.seek(0)
            json.dump(data, f, indent=2)
        else:
            # تحديث آخر ظهور
            data["users"][str(user_id)]["last_seen"] = str(datetime.now())
            f.seek(0)
            json.dump(data, f, indent=2)

def update_stats(user_id, platform):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        today = str(datetime.now().date())
        if data["last_date"] != today:
            data["daily"] = 0
            data["last_date"] = today
        
        if str(user_id) in data["users"]:
            user = data["users"][str(user_id)]
            user["downloads"] += 1
            user["last_seen"] = str(datetime.now())
            
            # تحديث إحصائيات المنصات
            if platform in user["platforms"]:
                user["platforms"][platform] += 1
            else:
                user["platforms"][platform] = 1
            
            # تحديث المنصة المفضلة
            user["fav_platform"] = max(user["platforms"], key=user["platforms"].get)
            
            data["total"] += 1
            data["daily"] += 1
            f.seek(0)
            json.dump(data, f, indent=2)

def get_users():
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
        return [uid for uid, u in data["users"].items() if not u.get("blocked", False)]

def get_all_users():
    with open(DB_FILE, 'r') as f:
        return list(json.load(f)["users"].keys())

def is_blocked(user_id):
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
        return data["users"].get(str(user_id), {}).get("blocked", False)

def block_user(user_id):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["blocked"] = True
            f.seek(0)
            json.dump(data, f, indent=2)
            return True
    return False

def unblock_user(user_id):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["blocked"] = False
            f.seek(0)
            json.dump(data, f, indent=2)
            return True
    return False

def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_top_users(limit=10):
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    users = data["users"]
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("downloads", 0), reverse=True)
    return sorted_users[:limit]

def get_uptime():
    now = datetime.now()
    diff = now - START_TIME
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    seconds = diff.seconds % 60
    if days > 0:
        return f"{days} يوم, {hours} ساعة, {minutes} دقيقة"
    else:
        return f"{hours} ساعة, {minutes} دقيقة, {seconds} ثانية"

# ========== أزرار فخمة ==========
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 تحميل فيديو", callback_data="help_video"),
         InlineKeyboardButton("🎵 استخراج صوت", callback_data="help_audio")],
        [InlineKeyboardButton("⚡ اختيار الجودة", callback_data="quality_menu"),
         InlineKeyboardButton("🎁 مشاركة البوت", callback_data="share_bot")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
         InlineKeyboardButton("❓ المساعدة", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 لوحة الأدمن", callback_data="admin_panel")],
        [InlineKeyboardButton("🎬 تحميل فيديو", callback_data="help_video"),
         InlineKeyboardButton("🎵 استخراج صوت", callback_data="help_audio")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
         InlineKeyboardButton("🎁 مشاركة البوت", callback_data="share_bot")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_panel():
    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats")],
        [InlineKeyboardButton("🏆 ترتيب المستخدمين", callback_data="admin_top")],
        [InlineKeyboardButton("📢 إعلان للجميع", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_block")],
        [InlineKeyboardButton("🔓 إلغاء حظر", callback_data="admin_unblock")],
        [InlineKeyboardButton("🗑️ حذف الكاش", callback_data="admin_clear")],
        [InlineKeyboardButton("🗑️ حذف كل المستخدمين", callback_data="admin_delete_all")],
        [InlineKeyboardButton("⏱️ وقت التشغيل", callback_data="admin_uptime")],
        [InlineKeyboardButton("📤 نسخة احتياطية", callback_data="admin_backup")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

def quality_keyboard():
    keyboard = [
        [InlineKeyboardButton("144p", callback_data="q_144"),
         InlineKeyboardButton("240p", callback_data="q_240"),
         InlineKeyboardButton("360p", callback_data="q_360")],
        [InlineKeyboardButton("480p", callback_data="q_480"),
         InlineKeyboardButton("720p 🔥", callback_data="q_720"),
         InlineKeyboardButton("1080p 👑", callback_data="q_1080")],
        [InlineKeyboardButton("🎵 صوت MP3", callback_data="q_audio")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== استخراج الرابط ==========
def extract_link(text):
    patterns = [
        r'(https?://(?:www\.)?tiktok\.com/[^\s]+)',
        r'(https?://vt\.tiktok\.com/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/watch\?v=[^\s&]+)',
        r'(https?://youtu\.be/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/shorts/[^\s]+)',
        r'(https?://(?:www\.)?facebook\.com/(?:watch|reel|share|share/r)/[^\s]+)',
        r'(https?://fb\.watch/[^\s]+)',
        r'(https?://[^\s]+)',
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(0)
    return None

def get_platform(url):
    if 'tiktok' in url:
        return 'TikTok'
    elif 'youtube' in url or 'youtu.be' in url:
        return 'YouTube'
    elif 'facebook.com' in url or 'fb.watch' in url:
        return 'Facebook'
    else:
        return 'Website'

# ========== تحميل تيك توك ==========
async def download_tiktok(url):
    opts = {
        'outtmpl': f'{DOWNLOADS_PATH}/tiktok_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'tiktok': {'without_watermark': ['true']}},
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'TikTok Video')
    except:
        opts['impersonate'] = 'chrome-120'
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'TikTok Video')

# ========== تحميل فيسبوك ==========
async def download_facebook(url):
    opts = {
        'outtmpl': f'{DOWNLOADS_PATH}/facebook_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        opts['format'] = 'best'
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            return path, info.get('title', 'Facebook Video')
    except:
        try:
            opts.pop('format', None)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                path = ydl.prepare_filename(info)
                return path, info.get('title', 'Facebook Video')
        except:
            opts['impersonate'] = 'chrome-120'
            opts['format'] = 'best'
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                path = ydl.prepare_filename(info)
                return path, info.get('title', 'Facebook Video')

# ========== تحميل يوتيوب ==========
async def download_other(url, quality=None, audio=False):
    quality_map = {
        '144': 'worst[height<=144]',
        '240': 'best[height<=240]',
        '360': 'best[height<=360]',
        '480': 'best[height<=480]',
        '720': 'best[height<=720]',
        '1080': 'best[height<=1080]',
    }
    
    if audio:
        opts = {
            'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        }
    else:
        fmt = quality_map.get(quality, 'best[height<=720]')
        opts = {
            'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': fmt,
            'merge_output_format': 'mp4',
        }
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
        if audio:
            path = path.rsplit('.', 1)[0] + '.mp3'
        return path, info.get('title', 'Media')

# ========== الدالة الرئيسية ==========
async def download_media(url, quality=None, audio=False):
    if is_music_platform(url):
        raise Exception("BANNED_PLATFORM")
    
    if 'tiktok.com' in url or 'vt.tiktok.com' in url:
        return await download_tiktok(url)
    elif 'facebook.com' in url or 'fb.watch' in url:
        return await download_facebook(url)
    else:
        return await download_other(url, quality, audio)

# ========== أوامر البوت ==========
async def start(update, context):
    u = update.effective_user
    
    # التحقق من الحظر
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك من استخدام البوت* 🚫\n\nللتواصل مع الدعم الفني", parse_mode='Markdown')
        return
    
    save_user(u.id, u.username)
    text = f"""
🖤 *أهلاً {u.first_name}!* 🖤

✨ {SIGNATURE} ✨

📌 *قوانين البوت:*
✅ *المسموح:* TikTok - YouTube - Facebook
❌ *الممنوع:* SoundCloud - Spotify - Deezer - Anghami - Apple Music

🔥 *أرسل رابط فيديو وسأقوم بتحميله فوراً*

{get_response(WELCOME_RESPONSES, u.first_name)}
"""
    kb = admin_keyboard() if is_admin(u.id) else main_keyboard()
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=kb)

async def handle_message(update, context):
    u = update.effective_user
    
    # التحقق من الحظر
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك من استخدام البوت* 🚫", parse_mode='Markdown')
        return
    
    url = extract_link(update.message.text)
    quality = context.user_data.get('quality', '720')
    audio = context.user_data.get('audio', False)
    
    if not url:
        await update.message.reply_text("❌ لم أجد رابط صحيح\nأرسل رابط من TikTok - YouTube - Facebook", parse_mode='Markdown')
        return
    
    if is_music_platform(url):
        await update.message.reply_text(BANNED_MESSAGE, parse_mode='Markdown')
        return
    
    platform = get_platform(url)
    sticker = get_random_sticker("processing")
    processing_text = get_random_processing_text(u.first_name)
    s = await update.message.reply_text(f"{sticker} {processing_text}\n📱 المنصة: {platform}", parse_mode='Markdown')
    
    try:
        path, title = await download_media(url, quality, audio)
        size = os.path.getsize(path) / 1048576
        
        if audio:
            with open(path, 'rb') as f:
                await update.message.reply_audio(f, title=title[:50], caption=f"🎵 {title[:40]}\n\n{SIGNATURE}", parse_mode='Markdown')
        else:
            success_sticker = get_random_sticker("success")
            success_text = get_random_success_text()
            with open(path, 'rb') as f:
                await update.message.reply_video(
                    f, 
                    caption=f"{success_sticker} {success_text}\n\n🎬 *{title[:60]}*\n📦 `{size:.1f} MB`\n⚡ `{quality}p`\n📱 `{platform}`\n\n{SIGNATURE}", 
                    parse_mode='Markdown', 
                    supports_streaming=True
                )
        
        os.remove(path)
        update_stats(u.id, platform)
        await s.delete()
    except Exception as e:
        if str(e) == "BANNED_PLATFORM":
            await s.edit_text(BANNED_MESSAGE, parse_mode='Markdown')
        else:
            error_sticker = get_random_sticker("error")
            error_text = get_random_error_text()
            await s.edit_text(f"{error_sticker} *فشل التحميل*\n{error_text}\n```\n{str(e)[:100]}\n```\n🔄 جرب رابط آخر", parse_mode='Markdown')

async def audio_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك من استخدام البوت* 🚫", parse_mode='Markdown')
        return
    context.user_data['audio'] = True
    await update.message.reply_text("🎵 *وضع استخراج الصوت مفعل*\nأرسل رابط الفيديو", parse_mode='Markdown')

async def stats_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك من استخدام البوت* 🚫", parse_mode='Markdown')
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    user_data = data['users'].get(str(u.id), {})
    text = f"""📊 *إحصائياتك*
━━━━━━━━━━━━━━━━━━━
📥 *تحميلات:* {user_data.get('downloads', 0)}
⭐ *المنصة المفضلة:* {user_data.get('fav_platform', 'لا يوجد')}
🕒 *آخر ظهور:* {user_data.get('last_seen', 'اليوم')[:16]}

🌍 *البوت*
━━━━━━━━━━━━━━━━━━━
📥 *إجمالي:* {data['total']:,}
📈 *اليوم:* {data['daily']}

✨ {SIGNATURE} ✨
"""
    await update.message.reply_text(text, parse_mode='Markdown')

async def share_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك من استخدام البوت* 🚫", parse_mode='Markdown')
        return
    bot = await context.bot.get_me()
    link = f"https://t.me/{bot.username}"
    await update.message.reply_text(f"🎁 *شارك البوت*\n`{link}`\n\n{SIGNATURE}", parse_mode='Markdown')

async def top_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك من استخدام البوت* 🚫", parse_mode='Markdown')
        return
    
    top_users = get_top_users(10)
    if not top_users:
        await update.message.reply_text("🏆 *لا يوجد مستخدمين بعد*", parse_mode='Markdown')
        return
    
    text = "🏆 *ترتيب المستخدمين الأكثر نشاطاً* 🏆\n━━━━━━━━━━━━━━━━━━━\n"
    for i, (uid, info) in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
        text += f"{medal} *{info.get('name', 'Unknown')}* - 📥 {info.get('downloads', 0)} تحميل\n"
    text += f"\n✨ {SIGNATURE} ✨"
    await update.message.reply_text(text, parse_mode='Markdown')

# ========== أوامر الأدمن ==========
async def admin_stats(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    blocked_count = sum(1 for u in data["users"].values() if u.get("blocked", False))
    text = f"""👑 *إحصائيات البوت* 👑
━━━━━━━━━━━━━━━━━━━
👥 *المستخدمين:* {len(data['users'])}
🚫 *محظورين:* {blocked_count}
📥 *إجمالي التحميلات:* {data['total']:,}
📈 *تحميلات اليوم:* {data['daily']}

✨ {SIGNATURE} ✨
"""
    await update.message.reply_text(text, parse_mode='Markdown')

async def admin_top(update, context):
    if not is_admin(update.effective_user.id):
        return
    top_users = get_top_users(10)
    if not top_users:
        await update.message.reply_text("🏆 *لا يوجد مستخدمين بعد*", parse_mode='Markdown')
        return
    
    text = "👑 *ترتيب المستخدمين الأكثر نشاطاً* 👑\n━━━━━━━━━━━━━━━━━━━\n"
    for i, (uid, info) in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
        status = "🚫" if info.get("blocked", False) else "✅"
        text += f"{medal} `{uid}` - {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)} | ⭐ {info.get('fav_platform', '-')}\n"
    text += f"\n✨ {SIGNATURE} ✨"
    await update.message.reply_text(text, parse_mode='Markdown')

async def broadcast_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("📢 /broadcast <الرسالة>")
        return
    s = await update.message.reply_text("🔄 جاري الإرسال...")
    users = get_users()
    sent = 0
    failed = 0
    for uid in users:
        try:
            await context.bot.send_message(int(uid), f"📢 *إعلان من الأدمن* 📢\n━━━━━━━━━━━━━━━━━━━\n{msg}\n━━━━━━━━━━━━━━━━━━━\n{SIGNATURE}", parse_mode='Markdown')
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    await s.edit_text(f"✅ تم الإرسال\n📨 نجح: {sent}\n❌ فشل: {failed}")

async def users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    txt = "👥 *قائمة المستخدمين*\n━━━━━━━━━━━━━━━━━━━\n"
    for uid, info in list(data['users'].items())[:30]:
        status = "🚫" if info.get("blocked", False) else "✅"
        txt += f"• `{uid}` - {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)} | ⭐ {info.get('fav_platform', '-')}\n"
    await update.message.reply_text(txt, parse_mode='Markdown')

async def clear_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    c = 0
    for f in os.listdir(DOWNLOADS_PATH):
        try:
            os.remove(os.path.join(DOWNLOADS_PATH, f))
            c += 1
        except:
            pass
    await update.message.reply_text(f"🗑️ *تم حذف {c} ملف مؤقت*\n\n{SIGNATURE}", parse_mode='Markdown')

async def delete_all_users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'w') as f:
        json.dump({"users": {}, "total": 0, "daily": 0, "last_date": str(datetime.now().date())}, f, indent=2)
    await update.message.reply_text(f"🗑️ *تم حذف جميع المستخدمين*\n\n{SIGNATURE}", parse_mode='Markdown')

async def uptime_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    uptime = get_uptime()
    await update.message.reply_text(f"⏱️ *وقت تشغيل البوت*\n━━━━━━━━━━━━━━━━━━━\n{uptime}\n━━━━━━━━━━━━━━━━━━━\n{SIGNATURE}", parse_mode='Markdown')

async def backup_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy(DB_FILE, backup_file)
    await update.message.reply_document(open(backup_file, 'rb'), caption=f"📦 *نسخة احتياطية*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{SIGNATURE}", parse_mode='Markdown')
    os.remove(backup_file)

async def block_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("🚫 /block <user_id>\n\nمثال: `/block 123456789`", parse_mode='Markdown')
        return
    user_id = context.args[0]
    if block_user(user_id):
        await update.message.reply_text(f"✅ *تم حظر المستخدم* `{user_id}`\n\n{SIGNATURE}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ *المستخدم* `{user_id}` *غير موجود*", parse_mode='Markdown')

async def unblock_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("🔓 /unblock <user_id>\n\nمثال: `/unblock 123456789`", parse_mode='Markdown')
        return
    user_id = context.args[0]
    if unblock_user(user_id):
        await update.message.reply_text(f"✅ *تم إلغاء حظر المستخدم* `{user_id}`\n\n{SIGNATURE}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ *المستخدم* `{user_id}` *غير موجود*", parse_mode='Markdown')

# ========== معالجة الأزرار ==========
async def callback(update, context):
    q = update.callback_query
    await q.answer()
    u = update.effective_user.id
    
    if q.data.startswith('q_'):
        val = q.data[2:]
        if val == 'audio':
            context.user_data['audio'] = True
            await q.edit_message_text("🎵 وضع الصوت مفعل", parse_mode='Markdown')
        else:
            context.user_data['quality'] = val
            context.user_data['audio'] = False
            await q.edit_message_text(f"⚡ تم ضبط الجودة {val}p", parse_mode='Markdown')
    
    elif q.data == 'quality_menu':
        await q.edit_message_text("⚡ *اختر الجودة:*", parse_mode='Markdown', reply_markup=quality_keyboard())
    
    elif q.data == 'share_bot':
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}"
        await q.edit_message_text(f"🎁 *رابط البوت:*\n`{link}`\n\n{SIGNATURE}", parse_mode='Markdown')
    
    elif q.data == 'my_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        user_data = data['users'].get(str(u), {})
        text = f"📊 *إحصائياتك*\n━━━━━━━━━━━━━━━━━━━\n📥 تحميلات: {user_data.get('downloads', 0)}\n⭐ المنصة المفضلة: {user_data.get('fav_platform', 'لا يوجد')}\n\n🌍 إجمالي البوت: {data['total']:,}\n📈 اليوم: {data['daily']}"
        await q.edit_message_text(text, parse_mode='Markdown')
    
    elif q.data == 'admin_panel':
        if is_admin(u):
            await q.edit_message_text("👑 *لوحة تحكم الأدمن* 👑\n━━━━━━━━━━━━━━━━━━━\nاختر الأمر المناسب:", parse_mode='Markdown', reply_markup=admin_panel())
        else:
            await q.edit_message_text("⛔ *غير مصرح* ⛔\nهذه اللوحة مخصصة للأدمن فقط", parse_mode='Markdown')
    
    elif q.data == 'admin_stats':
        if not is_admin(u):
            return
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        blocked_count = sum(1 for user in data["users"].values() if user.get("blocked", False))
        text = f"👑 *إحصائيات البوت*\n━━━━━━━━━━━━━━━━━━━\n👥 المستخدمين: {len(data['users'])}\n🚫 محظورين: {blocked_count}\n📥 إجمالي التحميلات: {data['total']:,}\n📈 اليوم: {data['daily']}"
        await q.edit_message_text(text, parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_top':
        if not is_admin(u):
            return
        top_users = get_top_users(10)
        if not top_users:
            await q.edit_message_text("🏆 لا يوجد مستخدمين بعد", parse_mode='Markdown', reply_markup=admin_panel())
            return
        text = "👑 *ترتيب المستخدمين الأكثر نشاطاً* 👑\n━━━━━━━━━━━━━━━━━━━\n"
        for i, (uid, info) in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
            status = "🚫" if info.get("blocked", False) else "✅"
            text += f"{medal} {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)} | ⭐ {info.get('fav_platform', '-')}\n"
        await q.edit_message_text(text, parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_broadcast':
        await q.edit_message_text("📢 *إرسال إعلان*\n━━━━━━━━━━━━━━━━━━━\nاستخدم الأمر:\n`/broadcast الرسالة`\n\nمثال:\n`/broadcast مرحباً بالجميع`", parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_users':
        if not is_admin(u):
            return
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        txt = "👥 *قائمة المستخدمين*\n━━━━━━━━━━━━━━━━━━━\n"
        for uid, info in list(data['users'].items())[:20]:
            status = "🚫" if info.get("blocked", False) else "✅"
            txt += f"• `{uid}` - {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)}\n"
        await q.edit_message_text(txt, parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_block':
        await q.edit_message_text("🚫 *حظر مستخدم*\n━━━━━━━━━━━━━━━━━━━\nاستخدم الأمر:\n`/block <user_id>`\n\nللعثور على user_id، استخدم أمر `/users`", parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_unblock':
        await q.edit_message_text("🔓 *إلغاء حظر مستخدم*\n━━━━━━━━━━━━━━━━━━━\nاستخدم الأمر:\n`/unblock <user_id>`\n\nللعثور على user_id، استخدم أمر `/users`", parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_clear':
        if not is_admin(u):
            return
        c = 0
        for f in os.listdir(DOWNLOADS_PATH):
            try:
                os.remove(os.path.join(DOWNLOADS_PATH, f))
                c += 1
            except:
                pass
        await q.edit_message_text(f"🗑️ *تم حذف {c} ملف مؤقت*", parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_delete_all':
        if not is_admin(u):
            return
        with open(DB_FILE, 'w') as f:
            json.dump({"users": {}, "total": 0, "daily": 0, "last_date": str(datetime.now().date())}, f, indent=2)
        await q.edit_message_text("🗑️ *تم حذف جميع المستخدمين*", parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_uptime':
        if not is_admin(u):
            return
        uptime = get_uptime()
        await q.edit_message_text(f"⏱️ *وقت تشغيل البوت*\n━━━━━━━━━━━━━━━━━━━\n{uptime}", parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_backup':
        if not is_admin(u):
            return
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy(DB_FILE, backup_file)
        await q.message.reply_document(open(backup_file, 'rb'), caption=f"📦 *نسخة احتياطية*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{SIGNATURE}", parse_mode='Markdown')
        os.remove(backup_file)
        await q.edit_message_text("📤 *تم إرسال النسخة الاحتياطية*", parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'help_video':
        await q.edit_message_text("🎬 *تحميل فيديو*\n━━━━━━━━━━━━━━━━━━━\n📤 أرسل رابط الفيديو مباشرة وسأقوم بتحميله بأعلى جودة\n\n✅ المنصات المدعومة:\n• TikTok (بدون علامة مائية)\n• YouTube\n• Facebook", parse_mode='Markdown')
    
    elif q.data == 'help_audio':
        await q.edit_message_text("🎵 *استخراج الصوت*\n━━━━━━━━━━━━━━━━━━━\n📤 استخدم الأمر `/audio` ثم أرسل رابط الفيديو\n\n🎧 سأرسل لك ملف MP3 بجودة عالية", parse_mode='Markdown')
    
    elif q.data == 'help':
        await q.edit_message_text("📌 *المساعدة*\n━━━━━━━━━━━━━━━━━━━\n🎬 *تحميل:* أرسل الرابط مباشرة\n🎵 *صوت:* /audio ثم الرابط\n⚡ *جودة:* اختر من القائمة\n📊 *إحصائيات:* /stats\n🎁 *مشاركة:* /share\n\n🚫 *ممنوع:* منصات الأغاني", parse_mode='Markdown')
    
    elif q.data == 'back':
        kb = admin_keyboard() if is_admin(u) else main_keyboard()
        await q.edit_message_text("🖤 *القائمة الرئيسية* 🖤", reply_markup=kb, parse_mode='Markdown')

# ========== التشغيل ==========
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    # أوامر البوت
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", audio_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("share", share_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    
    # أوامر الأدمن
    app.add_handler(CommandHandler("adminstats", admin_stats))
    app.add_handler(CommandHandler("admintop", admin_top))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("deleteusers", delete_all_users_cmd))
    app.add_handler(CommandHandler("uptime", uptime_cmd))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("block", block_user_cmd))
    app.add_handler(CommandHandler("unblock", unblock_user_cmd))
    
    # معالجات
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print(f"✨ {SIGNATURE} ✨")
    print("🔥 البوت الفاخر شغال يا باشا!")
    print(f"👑 الأدمن: {ADMIN_IDS}")
    print(f"📦 الإصدار: {VERSION}")
    print("✅ المسموح: TikTok | YouTube | Facebook")
    print("🚫 الممنوع: SoundCloud | Spotify | Deezer | Anghami | Apple Music")
    print("🎨 ستيكرات ورسائل عشوائية مفعلة")
    print("👥 نظام حظر وتتبع المستخدمين مفعل")
    print("=" * 60)
    app.run_polling()

if __name__ == "__main__":
    main()
