# main.py - منع تحميل الأغاني نهائياً
import os
import re
import json
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

from config import BOT_TOKEN, ADMIN_IDS, MAX_FILE_SIZE_MB, DOWNLOADS_PATH

# ========== إعدادات أولية ==========
os.makedirs(DOWNLOADS_PATH, exist_ok=True)

SIGNATURE = "✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨"
VERSION = "FINAL_10.0"

# ========== المنصات الممنوعة (أغاني) ==========
BANNED_PLATFORMS = [
    'soundcloud', 'spotify', 'deezer', 'anghami', 'apple music',
    'tidal', 'amazon music', 'youtube music', 'saavn', 'jio saavn',
    'gaana', 'wynk', 'hungama', 'boomplay', 'audiomack', 'bandcamp',
    'mixcloud', 'hearthis', 'reverbnation', 'datpiff', 'spinrilla'
]

# ========== ردود مصرية فاخرة مع تحذير ==========
WELCOME_RESPONSES = [
    "🎬 اهلاً بيك يا باشا {name}! 🤍\n\n⚠️ *تنبيه مهم:* البوت مخصص لتحميل الفيديوهات فقط! 🚫\n❌ ممنوع تحميل الأغاني من أي منصة (SoundCloud, Spotify, إلخ)",
    "💫 نورت يا فنان {name}! 🌟\n\n🎯 *ملاحظة:* احنا بنحمّل فيديوهات بس! 📹\n🚫 أي محاولة لتحميل أغاني هتترفض فوراً",
    "🔥 يا مرحباً يا كبير {name}! 😎\n\n📌 *تنبيه:* البوت للفيديوهات فقط من يوتيوب، فيسبوك، تيك توك، إنستا، تويتر\n❌ مفيش أغاني خالص!",
]

PROCESSING_RESPONSES = [
    "⚡ شوية صبر يا حبيب قلبى... 🎬",
    "🔥 جاري التحميل يا كبير... 💫",
]

SUCCESS_RESPONSES = [
    f"✅ تم يا فنان!\n{SIGNATURE}",
    f"🎬 خد الفيديو يا باشا!\n{SIGNATURE}",
]

BANNED_MESSAGE = """
🚫 *عذراً يا باشا!* 🚫

╔══════════════════════╗
║  ❌ منصة أغاني ❌     ║
╚══════════════════════╝

🎵 *البوت مخصص للفيديوهات فقط!*

✅ *المسموح:*
• TikTok 🎬
• YouTube 🎬
• Instagram 📸
• Facebook 📘
• Twitter 🐦

❌ *الممنوع (أغاني):*
• SoundCloud 🎵
• Spotify 🎧
• Deezer 📀
• Anghami 🎶
• Apple Music 🍎
• وأي منصة أغاني أخرى

💡 جرب رابط فيديو بدلاً من كده 🤍
{SIGNATURE}
"""

def get_response(responses, name=None):
    text = responses[datetime.now().second % len(responses)]
    return text.format(name=name) if name else text

def is_music_platform(url):
    """التحقق إذا كان الرابط من منصة أغاني"""
    url_lower = url.lower()
    for platform in BANNED_PLATFORMS:
        if platform in url_lower:
            return True
    return False

# ========== قاعدة بيانات ==========
DB_FILE = "bot_database.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"users": {}, "total": 0, "daily": 0, "last_date": str(datetime.now().date())}, f, indent=2)

def save_user(user_id, username):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {"name": username, "date": str(datetime.now()), "downloads": 0}
            f.seek(0)
            json.dump(data, f, indent=2)

def update_stats(user_id):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        today = str(datetime.now().date())
        if data["last_date"] != today:
            data["daily"] = 0
            data["last_date"] = today
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["downloads"] += 1
            data["total"] += 1
            data["daily"] += 1
            f.seek(0)
            json.dump(data, f, indent=2)

def get_users():
    with open(DB_FILE, 'r') as f:
        return list(json.load(f)["users"].keys())

def is_admin(user_id):
    return user_id in ADMIN_IDS

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
        [InlineKeyboardButton("📢 إعلان", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("🗑️ حذف الكاش", callback_data="admin_clear")],
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

# ========== تحميل المنصات الأخرى ==========
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

# ========== الدالة الرئيسية مع منع الأغاني ==========
async def download_media(url, quality=None, audio=False):
    # التحقق من منصات الأغاني الممنوعة
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
    save_user(u.id, u.username)
    text = f"""
🖤 *أهلاً {u.first_name}!* 🖤

{SIGNATURE}

📌 *قوانين البوت:*
✅ *المسموح:* TikTok - YouTube - Instagram - Facebook - Twitter
❌ *الممنوع:* SoundCloud - Spotify - Deezer - Anghami - Apple Music (أي منصة أغاني)

🔥 *أرسل رابط فيديو وسأقوم بتحميله فوراً*

{get_response(WELCOME_RESPONSES, u.first_name)}
"""
    kb = admin_keyboard() if is_admin(u.id) else main_keyboard()
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=kb)

async def handle_message(update, context):
    u = update.effective_user
    url = extract_link(update.message.text)
    quality = context.user_data.get('quality', '720')
    audio = context.user_data.get('audio', False)
    
    if not url:
        await update.message.reply_text("❌ لم أجد رابط صحيح\nأرسل رابط من TikTok - YouTube - Instagram - Facebook - Twitter", parse_mode='Markdown')
        return
    
    # التحقق من منصات الأغاني الممنوعة
    if is_music_platform(url):
        await update.message.reply_text(BANNED_MESSAGE, parse_mode='Markdown')
        return
    
    platform = get_platform(url)
    s = await update.message.reply_text(f"🔄 {get_response(PROCESSING_RESPONSES)}\n📱 المنصة: {platform}", parse_mode='Markdown')
    
    try:
        path, title = await download_media(url, quality, audio)
        size = os.path.getsize(path) / 1048576
        
        if audio:
            with open(path, 'rb') as f:
                await update.message.reply_audio(f, title=title[:50], caption=f"🎵 {title[:40]}\n\n{SIGNATURE}", parse_mode='Markdown')
        else:
            with open(path, 'rb') as f:
                await update.message.reply_video(f, caption=f"🎬 *{title[:60]}*\n📦 `{size:.1f} MB`\n⚡ `{quality}p`\n📱 `{platform}`\n\n{SIGNATURE}", parse_mode='Markdown', supports_streaming=True)
        
        os.remove(path)
        update_stats(u.id)
        await s.delete()
    except Exception as e:
        if str(e) == "BANNED_PLATFORM":
            await s.edit_text(BANNED_MESSAGE, parse_mode='Markdown')
        else:
            await s.edit_text(f"❌ *فشل التحميل*\n```\n{str(e)[:150]}\n```\n🔄 جرب رابط آخر", parse_mode='Markdown')

async def audio_cmd(update, context):
    context.user_data['audio'] = True
    await update.message.reply_text("🎵 *وضع استخراج الصوت مفعل*\nأرسل رابط الفيديو", parse_mode='Markdown')

async def stats_cmd(update, context):
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    u = data['users'].get(str(update.effective_user.id), {})
    await update.message.reply_text(f"📊 *إحصائياتك*\n• تحميلات: {u.get('downloads', 0)}\n\n🌍 *البوت*\n• إجمالي: {data['total']:,}\n• اليوم: {data['daily']}\n\n{SIGNATURE}", parse_mode='Markdown')

async def share_cmd(update, context):
    bot = await context.bot.get_me()
    link = f"https://t.me/{bot.username}"
    await update.message.reply_text(f"🎁 *شارك البوت*\n`{link}`\n\n{SIGNATURE}", parse_mode='Markdown')

# ========== أوامر الأدمن ==========
async def admin_stats(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    await update.message.reply_text(f"👑 *إحصائيات البوت*\n👥 مستخدمين: {len(data['users'])}\n📥 تحميلات: {data['total']}\n📈 اليوم: {data['daily']}\n\n{SIGNATURE}", parse_mode='Markdown')

async def broadcast_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("📢 /broadcast الرسالة")
        return
    s = await update.message.reply_text("🔄 جاري...")
    users = get_users()
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(int(uid), f"📢 *إعلان*\n\n{msg}\n\n{SIGNATURE}", parse_mode='Markdown')
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await s.edit_text(f"✅ تم الإرسال لـ {sent} مستخدم")

async def users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    txt = "👥 *المستخدمين:*\n"
    for uid, info in list(data['users'].items())[:30]:
        txt += f"• `{uid}` - {info['name']} - 📥 {info['downloads']}\n"
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
    await update.message.reply_text(f"🗑️ تم حذف {c} ملف مؤقت")

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
        await q.edit_message_text("اختر الجودة:", reply_markup=quality_keyboard())
    
    elif q.data == 'share_bot':
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}"
        await q.edit_message_text(f"🎁 *رابط البوت:*\n`{link}`\n\n{SIGNATURE}", parse_mode='Markdown')
    
    elif q.data == 'my_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        d = data['users'].get(str(u), {})
        await q.edit_message_text(f"📊 *إحصائياتك*\n📥 تحميلات: {d.get('downloads', 0)}\n🌍 إجمالي البوت: {data['total']:,}", parse_mode='Markdown')
    
    elif q.data == 'admin_panel':
        if is_admin(u):
            await q.edit_message_text("👑 لوحة الأدمن", reply_markup=admin_panel())
        else:
            await q.edit_message_text("⛔ غير مصرح")
    
    elif q.data == 'admin_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        await q.edit_message_text(f"👑 مستخدمين: {len(data['users'])}\n📥 تحميلات: {data['total']}\n📈 اليوم: {data['daily']}", reply_markup=admin_panel())
    
    elif q.data == 'admin_broadcast':
        await q.edit_message_text("📢 استخدم /broadcast الرسالة")
    
    elif q.data == 'admin_users':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        txt = "👥 المستخدمين:\n"
        for uid, info in list(data['users'].items())[:20]:
            txt += f"• {info['name']} - 📥 {info['downloads']}\n"
        await q.edit_message_text(txt, parse_mode='Markdown')
    
    elif q.data == 'admin_clear':
        c = 0
        for f in os.listdir(DOWNLOADS_PATH):
            try:
                os.remove(os.path.join(DOWNLOADS_PATH, f))
                c += 1
            except:
                pass
        await q.edit_message_text(f"🗑️ حذف {c} ملف", reply_markup=admin_panel())
    
    elif q.data == 'help_video':
        await q.edit_message_text("🎬 أرسل رابط الفيديو مباشرة", parse_mode='Markdown')
    
    elif q.data == 'help_audio':
        await q.edit_message_text("🎵 استخدم /audio ثم أرسل الرابط", parse_mode='Markdown')
    
    elif q.data == 'help':
        await q.edit_message_text("📌 *المساعدة*\n\n• أرسل رابط فيديو للتحميل\n• /audio لاستخراج الصوت\n• /stats للإحصائيات\n• /share لمشاركة البوت\n\n🚫 *ممنوع:* منصات الأغاني", parse_mode='Markdown')
    
    elif q.data == 'back':
        kb = admin_keyboard() if is_admin(u) else main_keyboard()
        await q.edit_message_text("🖤 القائمة الرئيسية", reply_markup=kb, parse_mode='Markdown')

# ========== التشغيل ==========
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", audio_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("share", share_cmd))
    app.add_handler(CommandHandler("adminstats", admin_stats))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 60)
    print(f"✨ {SIGNATURE} ✨")
    print("🔥 البوت الفاخر شغال يا باشا!")
    print(f"👑 الأدمن: {ADMIN_IDS}")
    print(f"📦 الإصدار: {VERSION}")
    print("✅ المسموح: TikTok | YouTube | Instagram | Facebook | Twitter")
    print("🚫 الممنوع: SoundCloud | Spotify | Deezer | Anghami | Apple Music")
    print("=" * 60)
    app.run_polling()

if __name__ == "__main__":
    main()
