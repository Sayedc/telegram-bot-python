# main.py - البوت الفاخر النهائي (النسخة المتطورة)
import os
import re
import json
import asyncio
import random
import shutil
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

from config import BOT_TOKEN, ADMIN_IDS, MAX_FILE_SIZE_MB, DOWNLOADS_PATH

# ========== استيراد الملفات الجديدة ==========
from downloader import Downloader
from metrics import Metrics
from security import is_safe_url, record_failed_attempt, is_user_blocked, get_failed_stats
from rate_limiter import RateLimiter

# ========== إعداد مجلد التحميلات (عشان Railway) ==========
if os.path.isfile(DOWNLOADS_PATH):
    os.remove(DOWNLOADS_PATH)
os.makedirs(DOWNLOADS_PATH, exist_ok=True)
START_TIME = datetime.now()

SIGNATURE = "✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨"
VERSION = "FINAL_10.0"

# ========== تهيئة المكونات الجديدة ==========
downloader = Downloader(DOWNLOADS_PATH, max_concurrent=3)
metrics = Metrics()
rate_limiter = RateLimiter(max_requests=10, time_window=60)

# ========== ستيكرات ورسائل ==========
STICKERS = {
    "processing": ["🔄", "⚙️", "⏳", "⌛", "📥", "🔧", "⚡", "💨", "🚀", "🎬", "📀", "⏰", "🕒", "🔁", "🌀"],
    "success": ["🎉", "✅", "🤍", "🔥", "💎", "⭐", "🏆", "🎬", "📀", "⚡", "💫", "🌟", "🍿", "🎥", "📹"],
    "error": ["❌", "⚠️", "🚫", "💔", "😅", "🤦", "🙈", "🥲", "🔁"]
}

PROCESSING_TEXTS = [
    "يتم التحميل يا {name} ⚡",
    "شوية صبر يا {name} 🎬",
    "على توكل على الله يا {name} 🚀",
    "استنى بس يا {name} 🤍",
    "جهز نفسك يا {name} 🔥",
    "خلصنا يا {name} تقريباً 💫",
]

SUCCESS_TEXTS = [
    "🎬 خد الفيديو يا باشا",
    "✅ تم يا فنان",
    "🔥 ألف هنا",
    "💎 استلم وادعيلي",
]

ERROR_TEXTS = [
    "❌ معلش الفيديو معدش موجود",
    "⚠️ حاجة غلطت، جرب فيديو تاني",
    "🚫 جرب رابط آخر",
]

WELCOME_RESPONSES = [
    "🎬 اهلاً بيك يا باشا {name}! 🤍\n\n🌍 *البوت بينزل أي حاجة من أي موقع*",
    "💫 نورت يا فنان {name}! 🌟\n\n🎯 *أرسل أي رابط وسأقوم بتحميله*",
    "🔥 يا مرحباً يا كبير {name}! 😎\n\n📌 *البوت شغال على كل المواقع*"
]

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

# ========== قاعدة بيانات ==========
DB_FILE = "bot_database.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"users": {}, "total": 0, "daily": 0, "last_date": str(datetime.now().date())}, f, indent=2)

async def save_user(user_id, username, context=None):
    is_new = False
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) not in data["users"]:
            is_new = True
            data["users"][str(user_id)] = {
                "name": username,
                "first_seen": str(datetime.now()),
                "last_seen": str(datetime.now()),
                "downloads": 0,
                "fav_platform": "None",
                "platforms": {},
                "blocked": False
            }
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
        else:
            data["users"][str(user_id)]["last_seen"] = str(datetime.now())
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    
    if is_new and context:
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"🆕 *مستخدم جديد* 🆕\n━━━━━━━━━━━━━━━━━━━\n👤 *الاسم:* {username}\n🆔 *ID:* `{user_id}`\n📅 *التاريخ:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n━━━━━━━━━━━━━━━━━━━\n{SIGNATURE}",
                    parse_mode='Markdown'
                )
            except:
                pass

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
            
            if platform in user["platforms"]:
                user["platforms"][platform] += 1
            else:
                user["platforms"][platform] = 1
            
            user["fav_platform"] = max(user["platforms"], key=user["platforms"].get) if user["platforms"] else "None"
            
            data["total"] += 1
            data["daily"] += 1
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

def delete_user_data(user_id):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) in data["users"]:
            downloads = data["users"][str(user_id)].get("downloads", 0)
            del data["users"][str(user_id)]
            data["total"] = max(0, data["total"] - downloads)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            return True
    return False

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
            f.truncate()
            return True
    return False

def unblock_user(user_id):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["blocked"] = False
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
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
    diff = datetime.now() - START_TIME
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    if hours > 0:
        return f"{hours} ساعة, {minutes} دقيقة"
    return f"{minutes} دقيقة"

# ========== معلومات الفيديو ==========
async def get_video_info(url):
    opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration = info.get('duration', 0)
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "غير معروف"
            
            filesize = info.get('filesize_approx', 0)
            if filesize:
                size_mb = filesize / 1048576
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "غير معروف"
            
            return {
                'title': info.get('title', 'غير معروف'),
                'duration': duration_str,
                'size': size_str,
            }
    except:
        return None

# ========== أزرار ==========
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
        [InlineKeyboardButton("📢 إعلان", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 حظر", callback_data="admin_block")],
        [InlineKeyboardButton("🔓 إلغاء حظر", callback_data="admin_unblock")],
        [InlineKeyboardButton("🗑️ حذف الكاش", callback_data="admin_clear")],
        [InlineKeyboardButton("🗑️ حذف الكل", callback_data="admin_delete_all")],
        [InlineKeyboardButton("⏱️ وقت التشغيل", callback_data="admin_uptime")],
        [InlineKeyboardButton("📤 نسخة احتياطية", callback_data="admin_backup")],
        [InlineKeyboardButton("📊 مقاييس الأداء", callback_data="admin_metrics")],
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
        r'(https?://(?:www\.)?instagram\.com/(?:p|reel|stories)/[^\s/?]+)',
        r'(https?://(?:www\.)?facebook\.com/(?:watch|reel|share|share/r)/[^\s]+)',
        r'(https?://fb\.watch/[^\s]+)',
        r'(https?://(?:www\.)?twitter\.com/[\w]+/status/[\d]+)',
        r'(https?://(?:www\.)?x\.com/[\w]+/status/[\d]+)',
        r'(https?://(?:www\.)?soundcloud\.com/[\w]+/[\w-]+)',
        r'(https?://(?:www\.)?spotify\.com/[\w]+/[\w-]+)',
        r'(https?://(?:www\.)?deezer\.com/[\w]+/[\w-]+)',
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
    elif 'instagram' in url:
        return 'Instagram'
    elif 'facebook.com' in url or 'fb.watch' in url:
        return 'Facebook'
    elif 'twitter.com' in url or 'x.com' in url:
        return 'Twitter'
    elif 'soundcloud' in url:
        return 'SoundCloud'
    elif 'spotify' in url:
        return 'Spotify'
    elif 'deezer' in url:
        return 'Deezer'
    else:
        return 'Website'

# ========== دوال التحميل ==========
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
            return ydl.prepare_filename(info), info.get('title', 'TikTok')
    except:
        opts['impersonate'] = 'chrome-120'
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'TikTok')

async def download_facebook(url):
    opts = {
        'outtmpl': f'{DOWNLOADS_PATH}/facebook_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info.get('title', 'Facebook')

async def download_other(url, quality='720', audio=False):
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
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
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

async def download_media(url, quality='720', audio=False):
    if 'tiktok.com' in url or 'vt.tiktok.com' in url:
        return await download_tiktok(url)
    elif 'facebook.com' in url or 'fb.watch' in url:
        return await download_facebook(url)
    else:
        return await download_other(url, quality, audio)

# ========== أوامر البوت ==========
async def start(update, context):
    u = update.effective_user
    
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك*", parse_mode='Markdown')
        return
    
    await save_user(u.id, u.username, context)
    text = f"""
🖤 *أهلاً {u.first_name}!* 🖤

✨ {SIGNATURE} ✨

🌍 *البوت بينزل أي حاجة من أي موقع*

📌 *المنصات المدعومة:*
• TikTok • YouTube • Instagram
• Facebook • Twitter • SoundCloud
• Spotify • Deezer • وأي موقع

🔥 *أرسل أي رابط وسأقوم بتحميله*

{get_response(WELCOME_RESPONSES, u.first_name)}
"""
    kb = admin_keyboard() if is_admin(u.id) else main_keyboard()
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=kb)

async def handle_message(update, context):
    u = update.effective_user
    start_time = datetime.now()
    
    # التحقق من الحظر المؤقت من security.py
    blocked, msg = is_user_blocked(u.id)
    if blocked:
        await update.message.reply_text(f"🚫 {msg}", parse_mode='Markdown')
        return
    
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك*", parse_mode='Markdown')
        return
    
    # Rate Limiting
    allowed, wait_time, remaining = rate_limiter.is_allowed(u.id)
    if not allowed:
        await update.message.reply_text(f"⏳ *تم تجاوز الحد المسموح*\nيرجى الانتظار {wait_time} ثانية\nالطلبات المتبقية: {remaining}", parse_mode='Markdown')
        return
    
    url = extract_link(update.message.text)
    quality = context.user_data.get('quality', '720')
    audio = context.user_data.get('audio', False)
    
    if not url:
        await update.message.reply_text("❌ أرسل رابط صحيح", parse_mode='Markdown')
        return
    
    # فحص أمان الرابط
    safe, msg = is_safe_url(url)
    if not safe:
        await update.message.reply_text(f"⚠️ {msg}", parse_mode='Markdown')
        return
    
    platform = get_platform(url)
    
    # عرض معلومات الفيديو
video_info = await get_video_info(url)

if video_info:
    await update.message.reply_text(
        f"📹 معلومات الفيديو\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📝 العنوان: {video_info['title'][:50]}\n"
        f"⏱️ المدة: {video_info['duration']}\n"
        f"📦 الحجم: {video_info['size']}\n"
        f"📱 المنصة: {platform}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 جاري التحميل...\n"
        f"📊 ترتيبك في قائمة الانتظار: "
        f"{downloader.get_queue_position(u.id) if downloader.queue.qsize() > 0 else 'جاري الآن'}"
    
    
    
    )

    # تسجيل زمن التحميل
    download_start = datetime.now()
    
    try:
        # استخدام نظام Queue للتحميل
        position = await downloader.add_to_queue(url, quality, audio, u.id)
        if position > 1:
            await s.edit_text(f"{sticker} {processing_text}\n📱 {platform}\n📊 ترتيبك: {position} في قائمة الانتظار")
        
        path, title = await downloader._download_media(url, quality, audio)
        size = os.path.getsize(path) / 1048576
        
        # تسجيل المقاييس
        elapsed = (datetime.now() - download_start).total_seconds()
        metrics.record_download(elapsed, platform, u.id)
        
        if audio:
            with open(path, 'rb') as f:
                await update.message.reply_audio(f, title=title[:50], caption=f"{get_random_success_text()}\n\n{SIGNATURE}", parse_mode='Markdown')
            context.user_data['audio'] = False
        else:
            with open(path, 'rb') as f:
                await update.message.reply_video(
                    f,
                    caption=f"{get_random_sticker('success')} {get_random_success_text()}\n\n🎬 *{title[:60]}*\n📦 `{size:.1f} MB`\n⚡ `{quality}p`\n📱 `{platform}`\n\n{SIGNATURE}",
                    parse_mode='Markdown',
                    supports_streaming=True
                )
        
        os.remove(path)
        update_stats(u.id, platform)
        await s.delete()
        
        # تسجيل زمن الاستجابة
        metrics.record_response((datetime.now() - start_time).total_seconds())
        
    except Exception as e:
        metrics.record_error(str(e)[:50], u.id)
        blocked, msg = record_failed_attempt(u.id, url)
        if blocked:
            await s.edit_text(f"🚫 {msg}", parse_mode='Markdown')
        else:
            await s.edit_text(f"{get_random_sticker('error')} {get_random_error_text()}\n```\n{str(e)[:100]}\n```\n{msg}", parse_mode='Markdown')

async def audio_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك*", parse_mode='Markdown')
        return
    context.user_data['audio'] = True
    await update.message.reply_text("🎵 *وضع الصوت مفعل*\nأرسل رابط الفيديو", parse_mode='Markdown')

async def stats_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك*", parse_mode='Markdown')
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    user_data = data['users'].get(str(u.id), {})
    remaining = rate_limiter.get_remaining(u.id)
    await update.message.reply_text(
        f"📊 *إحصائياتك*\n━━━━━━━━━━━━━━━━━━━\n📥 تحميلات: {user_data.get('downloads', 0)}\n⭐ المنصة المفضلة: {user_data.get('fav_platform', 'لا يوجد')}\n📊 الطلبات المتبقية اليوم: {remaining}\n\n🌍 إجمالي البوت: {data['total']:,}\n📈 اليوم: {data['daily']}\n\n{SIGNATURE}",
        parse_mode='Markdown'
    )

async def share_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك*", parse_mode='Markdown')
        return
    bot = await context.bot.get_me()
    await update.message.reply_text(f"🎁 *شارك البوت*\n`https://t.me/{bot.username}`\n\n{SIGNATURE}", parse_mode='Markdown')

async def top_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك*", parse_mode='Markdown')
        return
    
    top_users = get_top_users(10)
    if not top_users:
        await update.message.reply_text("🏆 *لا يوجد مستخدمين بعد*", parse_mode='Markdown')
        return
    
    text = "🏆 *الأكثر نشاطاً* 🏆\n━━━━━━━━━━━━━━━━━━━\n"
    for i, (uid, info) in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
        text += f"{medal} *{info.get('name', 'Unknown')}* - 📥 {info.get('downloads', 0)}\n"
    await update.message.reply_text(text + f"\n{SIGNATURE}", parse_mode='Markdown')

async def privacy_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك*", parse_mode='Markdown')
        return
    
    await update.message.reply_text(
        f"🔒 *سياسة الخصوصية*\n━━━━━━━━━━━━━━━━━━━\n📌 *البيانات المحفوظة:*\n• معرف المستخدم\n• اسم المستخدم\n• تاريخ الانضمام\n• عدد التحميلات\n\n📅 *مدة الحفظ:* 30 يوم\n🗑️ *مسح البيانات:* /delete_my_data\n\n✨ {SIGNATURE} ✨",
        parse_mode='Markdown'
    )

async def delete_my_data_cmd(update, context):
    u = update.effective_user
    if is_blocked(u.id):
        await update.message.reply_text("🚫 *لقد تم حظرك*", parse_mode='Markdown')
        return
    
    if delete_user_data(u.id):
        rate_limiter.reset_user(u.id)
        await update.message.reply_text(f"🗑️ *تم حذف بياناتك*\n\n{SIGNATURE}", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ *لا توجد بيانات*", parse_mode='Markdown')

# ========== أوامر الأدمن ==========
async def admin_stats(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    blocked_count = sum(1 for u in data["users"].values() if u.get("blocked", False))
    downloader_stats = downloader.get_stats()
    await update.message.reply_text(
        f"👑 *إحصائيات البوت*\n━━━━━━━━━━━━━━━━━━━\n👥 المستخدمين: {len(data['users'])}\n🚫 محظورين: {blocked_count}\n📥 إجمالي التحميلات: {data['total']:,}\n📈 اليوم: {data['daily']}\n⏱️ وقت التشغيل: {get_uptime()}\n\n📊 *نظام التحميل*\n📥 طلبات قيد الانتظار: {downloader_stats['queue_size']}\n⚡ تحميلات نشطة: {downloader_stats['active']}\n✅ نجح: {downloader_stats['success']}\n❌ فشل: {downloader_stats['failed']}\n⏱️ متوسط وقت التحميل: {downloader_stats['avg_time']} ثانية\n\n✨ {SIGNATURE} ✨",
        parse_mode='Markdown'
    )

async def admin_top(update, context):
    if not is_admin(update.effective_user.id):
        return
    top_users = get_top_users(10)
    if not top_users:
        await update.message.reply_text("🏆 *لا يوجد مستخدمين*", parse_mode='Markdown')
        return
    
    text = "👑 *ترتيب المستخدمين* 👑\n━━━━━━━━━━━━━━━━━━━\n"
    for i, (uid, info) in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
        status = "🚫" if info.get("blocked", False) else "✅"
        text += f"{medal} `{uid}` - {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)}\n"
    await update.message.reply_text(text + f"\n{SIGNATURE}", parse_mode='Markdown')

async def broadcast_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("📢 /broadcast <الرسالة>")
        return
    
    s = await update.message.reply_text("🔄 جاري...")
    users = get_users()
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(int(uid), f"📢 *إعلان*\n{msg}\n\n{SIGNATURE}", parse_mode='Markdown')
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await s.edit_text(f"✅ تم لـ {sent} مستخدم")

async def users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    txt = "👥 *المستخدمين*\n━━━━━━━━━━━━━━━━━━━\n"
    for uid, info in list(data['users'].items())[:30]:
        status = "🚫" if info.get("blocked", False) else "✅"
        txt += f"• `{uid}` - {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)}\n"
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
    await update.message.reply_text(f"🗑️ *حذف {c} ملف*", parse_mode='Markdown')

async def delete_all_users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    admin_id = str(update.effective_user.id)
    admin_name = None
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
        if admin_id in data["users"]:
            admin_name = data["users"][admin_id].get("name", "Admin")
    
    with open(DB_FILE, 'w') as f:
        if admin_name:
            json.dump({
                "users": {admin_id: {
                    "name": admin_name,
                    "first_seen": str(datetime.now()),
                    "last_seen": str(datetime.now()),
                    "downloads": 0,
                    "fav_platform": "None",
                    "platforms": {},
                    "blocked": False
                }},
                "total": 0,
                "daily": 0,
                "last_date": str(datetime.now().date())
            }, f, indent=2)
        else:
            json.dump({"users": {}, "total": 0, "daily": 0, "last_date": str(datetime.now().date())}, f, indent=2)
    await update.message.reply_text(f"🗑️ *تم حذف الكل (عدا الأدمن)*\n\n{SIGNATURE}", parse_mode='Markdown')

async def uptime_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(f"⏱️ *وقت التشغيل*\n━━━━━━━━━━━━━━━━━━━\n{get_uptime()}\n━━━━━━━━━━━━━━━━━━━\n{SIGNATURE}", parse_mode='Markdown')

async def backup_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    try:
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy(DB_FILE, backup_file)
        await update.message.reply_document(open(backup_file, 'rb'), caption=f"📦 *نسخة احتياطية*\n{SIGNATURE}", parse_mode='Markdown')
        os.remove(backup_file)
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)[:100]}")

async def block_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("🚫 /block <user_id>")
        return
    user_id = context.args[0]
    if block_user(user_id):
        await update.message.reply_text(f"✅ *تم حظر `{user_id}`*\n\n{SIGNATURE}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ *المستخدم غير موجود*", parse_mode='Markdown')

async def unblock_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("🔓 /unblock <user_id>")
        return
    user_id = context.args[0]
    if unblock_user(user_id):
        await update.message.reply_text(f"✅ *تم إلغاء حظر `{user_id}`*\n\n{SIGNATURE}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ *المستخدم غير موجود*", parse_mode='Markdown')

async def admin_metrics_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    summary = metrics.get_summary()
    downloader_stats = downloader.get_stats()
    failed_stats = get_failed_stats()
    
    await update.message.reply_text(
        f"📊 *مقاييس الأداء*\n━━━━━━━━━━━━━━━━━━━\n⏱️ متوسط زمن الاستجابة: {summary['avg_response']} ثانية\n⏱️ متوسط زمن التحميل: {summary['avg_download']} ثانية\n📈 نسبة النجاح: {summary['success_rate']}%\n🎯 أكثر منصة استخداماً: {summary['top_platform']}\n⚠️ أكثر خطأ شيوعاً: {summary['common_error']}\n\n📥 *نظام التحميل*\n⏳ طلبات منتظرة: {downloader_stats['queue_size']}\n⚡ تحميلات نشطة: {downloader_stats['active']}\n✅ نجح: {downloader_stats['success']}\n❌ فشل: {downloader_stats['failed']}\n\n🔒 *نظام الأمان*\n⚠️ محاولات فاشلة: {failed_stats['total_failed']}\n🚫 مستخدمين محظورين مؤقتاً: {failed_stats['blocked_users']}\n\n✨ {SIGNATURE} ✨",
        parse_mode='Markdown'
    )

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
            await q.edit_message_text(f"⚡ الجودة {val}p", parse_mode='Markdown')
    
    elif q.data == 'quality_menu':
        await q.edit_message_text("⚡ *اختر الجودة:*", parse_mode='Markdown', reply_markup=quality_keyboard())
    
    elif q.data == 'share_bot':
        bot = await context.bot.get_me()
        await q.edit_message_text(f"🎁 `https://t.me/{bot.username}`\n\n{SIGNATURE}", parse_mode='Markdown')
    
    elif q.data == 'my_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        user_data = data['users'].get(str(u), {})
        remaining = rate_limiter.get_remaining(u)
        await q.edit_message_text(f"📥 {user_data.get('downloads', 0)}\n🌍 {data['total']}\n📊 طلبات متبقية: {remaining}", parse_mode='Markdown')
    
    elif q.data == 'admin_panel':
        if is_admin(u):
            await q.edit_message_text("👑 *لوحة الأدمن*", parse_mode='Markdown', reply_markup=admin_panel())
        else:
            await q.edit_message_text("⛔ غير مصرح")
    
    elif q.data == 'admin_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        await q.edit_message_text(f"👥 {len(data['users'])}\n📥 {data['total']}\n📈 {data['daily']}", reply_markup=admin_panel())
    
    elif q.data == 'admin_top':
        top_users = get_top_users(10)
        if not top_users:
            await q.edit_message_text("🏆 لا يوجد", reply_markup=admin_panel())
            return
        text = "👑 *الترتيب*\n"
        for i, (uid, info) in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
            text += f"{medal} {info.get('name', 'Unknown')}\n   📥 {info.get('downloads', 0)}\n"
        await q.edit_message_text(text, parse_mode='Markdown', reply_markup=admin_panel())
    
    elif q.data == 'admin_broadcast':
        await q.edit_message_text("📢 /broadcast رسالة")
    
    elif q.data == 'admin_users':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        txt = "👥 *المستخدمين*\n"
        for uid, info in list(data['users'].items())[:20]:
            status = "🚫" if info.get("blocked", False) else "✅"
            txt += f"• {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)}\n"
        await q.edit_message_text(txt, parse_mode='Markdown')
    
    elif q.data == 'admin_block':
        await q.edit_message_text("🚫 /block <user_id>")
    
    elif q.data == 'admin_unblock':
        await q.edit_message_text("🔓 /unblock <user_id>")
    
    elif q.data == 'admin_clear':
        c = 0
        for f in os.listdir(DOWNLOADS_PATH):
            try:
                os.remove(os.path.join(DOWNLOADS_PATH, f))
                c += 1
            except:
                pass
        await q.edit_message_text(f"🗑️ {c} ملف", reply_markup=admin_panel())
    
    elif q.data == 'admin_delete_all':
        await delete_all_users_cmd(update, context)
    
    elif q.data == 'admin_uptime':
        await q.edit_message_text(f"⏱️ {get_uptime()}", reply_markup=admin_panel())
    
    elif q.data == 'admin_backup':
        await backup_cmd(update, context)
    
    elif q.data == 'admin_metrics':
        await admin_metrics_cmd(update, context)
    
    elif q.data == 'help_video':
        await q.edit_message_text("🎬 أرسل رابط الفيديو", parse_mode='Markdown')
    
    elif q.data == 'help_audio':
        await q.edit_message_text("🎵 /audio ثم الرابط", parse_mode='Markdown')
    
    elif q.data == 'help':
        await q.edit_message_text(
            "📌 *المساعدة*\n━━━━━━━━━━━━━━━━━━━\n🎬 تحميل: أرسل الرابط\n🎵 صوت: /audio ثم الرابط\n⚡ جودة: اختر من القائمة\n📊 إحصائيات: /stats\n🎁 مشاركة: /share\n🔒 خصوصية: /privacy\n🗑️ مسح بياناتي: /delete_my_data",
            parse_mode='Markdown'
        )
    
    elif q.data == 'back':
        kb = admin_keyboard() if is_admin(u) else main_keyboard()
        await q.edit_message_text("🖤 *القائمة الرئيسية*", reply_markup=kb, parse_mode='Markdown')

# ========== التشغيل ==========
async def start_downloader():
    await downloader.start()

def main():
    init_db()
    
    # تشغيل downloader في حدث asyncio منفصل
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(start_downloader())
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", audio_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("share", share_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("privacy", privacy_cmd))
    app.add_handler(CommandHandler("delete_my_data", delete_my_data_cmd))
    
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
    app.add_handler(CommandHandler("metrics", admin_metrics_cmd))
    
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print(f"✨ {SIGNATURE} ✨")
    print("🔥 البوت المتطور شغال يا باشا!")
    print(f"👑 الأدمن: {ADMIN_IDS}")
    print("🌍 بينزل أي حاجة من أي موقع")
    print("📊 نظام Queue و Rate Limiting مفعل")
    print("🔒 نظام أمان متقدم مفعل")
    print("=" * 60)
    app.run_polling()

if __name__ == "__main__":
    main()
