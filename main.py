# main.py - 𝓐𝓵𝓱𝓪𝔀𝔂 𝓓𝓸𝔀𝓷𝓵𝓸𝓪𝓭 - النسخة العالمية النهائية
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

# ========== إعدادات أولية ==========
os.makedirs(DOWNLOADS_PATH, exist_ok=True)
START_TIME = datetime.now()

SIGNATURE = "✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨"
VERSION = "GLOBAL_12.0"

# ========== ستيكرات ثابتة عشوائية ==========
STICKERS = {
    "processing": ["🔄", "⚙️", "⏳", "⌛", "📥", "🔧", "⚡", "💨", "🚀", "🎬", "📀", "⏰", "🕒", "🔁", "🌀"],
    "success": ["🎉", "✅", "🤍", "🔥", "💎", "⭐", "🏆", "🎬", "📀", "⚡", "💫", "🌟", "🍿", "🎥", "📹"],
    "error": ["❌", "⚠️", "🚫", "💔", "😅", "🤦", "🙈", "🥲", "🔁"]
}

# ========== كاموس للرسائل متعدد اللغات ==========
TEXTS = {
    "ar": {
        "processing": ["يتم التحميل يا {name} ⚡", "شوية صبر يا {name} 🎬", "على توكل على الله يا {name} 🚀", "استنى بس يا {name} 🤍", "جهز نفسك يا {name} 🔥"],
        "success": ["🎬 خد الفيديو يا باشا", "✅ تم يا فنان", "🔥 ألف هنا", "💎 استلم وادعيلي", "⭐ عقبال ما تسمعه", "🏆 تحفة يا باشا", "💫 الله ينور عليك"],
        "error": ["❌ معلش الفيديو معدش موجود", "⚠️ حاجة غلطت، جرب فيديو تاني", "🚫 جرب رابط آخر", "💔 الفيديو يمكن خاص أو اتحذف", "😅 حاول تاني يا كبير"],
        "welcome": ["🎬 اهلاً بيك يا باشا {name}! 🤍\n\n🌍 *البوت بينزل أي حاجة من أي موقع*", "💫 نورت يا فنان {name}! 🌟\n\n🎯 *أرسل أي رابط وسأقوم بتحميله*", "🔥 يا مرحباً يا كبير {name}! 😎\n\n📌 *البوت شغال على كل المواقع*"],
        "no_link": "❌ لم أجد رابط صحيح\nأرسل رابط من أي موقع",
        "blocked": "🚫 *لقد تم حظرك من استخدام البوت* 🚫\n\nللتواصل مع الدعم الفني",
        "deleted": "🗑️ *تم حذف بياناتك بنجاح*\n\n{SIGNATURE}",
        "not_found": "❌ لا توجد بيانات لك",
        "step1": "🔄 [1/4] جاري معالجة الرابط...\n📱 المنصة: {platform}",
        "step2": "⚡ [2/4] جاري التحميل من {platform}...\n⏳ يرجى الانتظار...",
        "step3": "💾 [3/4] اكتمل التحميل، جاري التجهيز للإرسال...\n📦 الحجم: {size} MB",
        "confirm": "✅ هل تريد متابعة التحميل؟",
        "confirm_yes": "✅ متابعة التحميل...",
        "confirm_no": "❌ تم إلغاء التحميل"
    },
    "en": {
        "processing": ["Downloading {name} ⚡", "Just a moment {name} 🎬", "Processing {name} 🚀", "Almost there {name} 🤍", "Getting ready {name} 🔥"],
        "success": ["🎬 Here's your video", "✅ Done!", "🔥 Enjoy", "💎 Download complete", "⭐ Here you go", "🏆 Check this out", "💫 All done"],
        "error": ["❌ Video not available", "⚠️ Something went wrong", "🚫 Try another link", "💔 Video may be private", "😅 Please try again"],
        "welcome": ["🎬 Welcome {name}! 🤍\n\n🌍 *Download anything from any website*", "💫 Hi {name}! 🌟\n\n🎯 *Send any link and I'll download it*", "🔥 Hey {name}! 😎\n\n📌 *Bot works on all platforms*"],
        "no_link": "❌ No valid link found\nSend a link from any website",
        "blocked": "🚫 *You have been blocked from using this bot* 🚫\n\nContact support",
        "deleted": "🗑️ *Your data has been deleted successfully*\n\n{SIGNATURE}",
        "not_found": "❌ No data found for you",
        "step1": "🔄 [1/4] Processing link...\n📱 Platform: {platform}",
        "step2": "⚡ [2/4] Downloading from {platform}...\n⏳ Please wait...",
        "step3": "💾 [3/4] Download complete, preparing to send...\n📦 Size: {size} MB",
        "confirm": "✅ Do you want to continue?",
        "confirm_yes": "✅ Continuing download...",
        "confirm_no": "❌ Download cancelled"
    }
}

def detect_language(text):
    """كشف اللغة من النص (عربي أو إنجليزي)"""
    if not text:
        return "ar"
    # كشف بسيط للغة العربية
    arabic_chars = re.findall(r'[\u0600-\u06FF]', text)
    if len(arabic_chars) > len(text) * 0.3:
        return "ar"
    return "en"

def get_text(key, lang="ar", **kwargs):
    """جلب النص باللغة المطلوبة"""
    text = TEXTS.get(lang, TEXTS["ar"]).get(key, TEXTS["ar"].get(key, ""))
    if kwargs:
        text = text.format(**kwargs)
    return text

def get_random_processing_text(name, lang="ar"):
    texts = TEXTS.get(lang, TEXTS["ar"]).get("processing", [])
    text = random.choice(texts)
    return text.format(name=name)

def get_random_success_text(lang="ar"):
    texts = TEXTS.get(lang, TEXTS["ar"]).get("success", [])
    return random.choice(texts)

def get_random_error_text(lang="ar"):
    texts = TEXTS.get(lang, TEXTS["ar"]).get("error", [])
    return random.choice(texts)

def get_random_sticker(category):
    return random.choice(STICKERS.get(category, ["🎉"]))

# ========== قاعدة بيانات ==========
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

def save_user(user_id, username, context=None):
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
                "blocked": False,
                "lang": "ar"
            }
            f.seek(0)
            json.dump(data, f, indent=2)
        else:
            data["users"][str(user_id)]["last_seen"] = str(datetime.now())
            f.seek(0)
            json.dump(data, f, indent=2)
    
    if is_new and context:
        for admin_id in ADMIN_IDS:
            try:
                context.bot.send_message(
                    admin_id,
                    f"🆕 *New user!* 🆕\n━━━━━━━━━━━━━━━━━━━\n👤 *Name:* {username}\n🆔 *ID:* `{user_id}`\n📅 *Date:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n━━━━━━━━━━━━━━━━━━━\n{SIGNATURE}",
                    parse_mode='Markdown'
                )
            except:
                pass

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

def delete_user_data(user_id):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) in data["users"]:
            downloads = data["users"][str(user_id)].get("downloads", 0)
            del data["users"][str(user_id)]
            data["total"] = max(0, data["total"] - downloads)
            f.seek(0)
            json.dump(data, f, indent=2)
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
        return f"{days} days, {hours} hours, {minutes} minutes"
    else:
        return f"{hours} hours, {minutes} minutes, {seconds} seconds"

# ========== دوال التحميل ==========
async def get_video_info(url):
    """جلب معلومات الفيديو"""
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
                duration_str = "N/A"
            
            filesize = info.get('filesize_approx', 0)
            if filesize:
                size_mb = filesize / 1048576
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "N/A"
            
            return {
                'title': info.get('title', 'N/A'),
                'duration': duration_str,
                'size': size_str,
                'uploader': info.get('uploader', 'N/A'),
                'platform': info.get('extractor_key', 'Website')
            }
    except:
        return None

async def download_media(url, quality=None, audio=False):
    """تحميل الوسائط من أي رابط"""
    quality_map = {
        '144': 'worst[height<=144]',
        '240': 'best[height<=240]',
        '360': 'best[height<=360]',
        '480': 'best[height<=480]',
        '720': 'best[height<=720]',
        '1080': 'best[height<=1080]',
    }
    
    # إعدادات الكوكيز لليوتيوب
    cookies_file = "cookies.txt"
    cookies_arg = {'cookiefile': cookies_file} if os.path.exists(cookies_file) else {}
    
    if audio:
        opts = {
            'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            **cookies_arg
        }
    else:
        fmt = quality_map.get(quality, 'best[height<=720]')
        opts = {
            'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': fmt,
            'merge_output_format': 'mp4',
            **cookies_arg
        }
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
        if audio:
            path = path.rsplit('.', 1)[0] + '.mp3'
        return path, info.get('title', 'Media')

# ========== استخراج الرابط ==========
def extract_link(text):
    """استخراج الرابط من النص"""
    patterns = [
        r'(https?://[^\s]+)',
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(0)
    return None

def get_platform(url):
    """تحديد المنصة من الرابط"""
    url_lower = url.lower()
    if 'tiktok' in url_lower:
        return 'TikTok'
    elif 'youtube' in url_lower or 'youtu.be' in url_lower:
        return 'YouTube'
    elif 'instagram' in url_lower:
        return 'Instagram'
    elif 'facebook' in url_lower or 'fb.watch' in url_lower:
        return 'Facebook'
    elif 'twitter' in url_lower or 'x.com' in url_lower:
        return 'Twitter'
    elif 'soundcloud' in url_lower:
        return 'SoundCloud'
    elif 'spotify' in url_lower:
        return 'Spotify'
    elif 'deezer' in url_lower:
        return 'Deezer'
    else:
        return 'Website'

# ========== أزرار فخمة ==========
def main_keyboard(lang="ar"):
    keyboard = [
        [InlineKeyboardButton(get_text("help_video", lang), callback_data="help_video"),
         InlineKeyboardButton(get_text("help_audio", lang), callback_data="help_audio")],
        [InlineKeyboardButton(get_text("quality_menu", lang), callback_data="quality_menu"),
         InlineKeyboardButton(get_text("share_bot", lang), callback_data="share_bot")],
        [InlineKeyboardButton(get_text("my_stats", lang), callback_data="my_stats"),
         InlineKeyboardButton(get_text("help", lang), callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_keyboard(lang="ar"):
    keyboard = [
        [InlineKeyboardButton(get_text("admin_panel", lang), callback_data="admin_panel")],
        [InlineKeyboardButton(get_text("help_video", lang), callback_data="help_video"),
         InlineKeyboardButton(get_text("help_audio", lang), callback_data="help_audio")],
        [InlineKeyboardButton(get_text("my_stats", lang), callback_data="my_stats"),
         InlineKeyboardButton(get_text("share_bot", lang), callback_data="share_bot")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_panel(lang="ar"):
    keyboard = [
        [InlineKeyboardButton(get_text("admin_stats", lang), callback_data="admin_stats")],
        [InlineKeyboardButton(get_text("admin_top", lang), callback_data="admin_top")],
        [InlineKeyboardButton(get_text("admin_broadcast", lang), callback_data="admin_broadcast")],
        [InlineKeyboardButton(get_text("admin_users", lang), callback_data="admin_users")],
        [InlineKeyboardButton(get_text("admin_block", lang), callback_data="admin_block")],
        [InlineKeyboardButton(get_text("admin_unblock", lang), callback_data="admin_unblock")],
        [InlineKeyboardButton(get_text("admin_clear", lang), callback_data="admin_clear")],
        [InlineKeyboardButton(get_text("admin_delete_all", lang), callback_data="admin_delete_all")],
        [InlineKeyboardButton(get_text("admin_uptime", lang), callback_data="admin_uptime")],
        [InlineKeyboardButton(get_text("admin_backup", lang), callback_data="admin_backup")],
        [InlineKeyboardButton(get_text("back", lang), callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

def quality_keyboard(lang="ar"):
    keyboard = [
        [InlineKeyboardButton("📱 144p", callback_data="q_144"),
         InlineKeyboardButton("📱 240p", callback_data="q_240"),
         InlineKeyboardButton("📱 360p", callback_data="q_360")],
        [InlineKeyboardButton("📺 480p", callback_data="q_480"),
         InlineKeyboardButton("📺 720p 🔥", callback_data="q_720"),
         InlineKeyboardButton("📺 1080p 👑", callback_data="q_1080")],
        [InlineKeyboardButton(get_text("audio", lang), callback_data="q_audio")],
        [InlineKeyboardButton(get_text("back", lang), callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(lang="ar"):
    keyboard = [
        [InlineKeyboardButton(get_text("confirm_yes", lang), callback_data="confirm_yes"),
         InlineKeyboardButton(get_text("confirm_no", lang), callback_data="confirm_no")],
    ]
    return InlineKeyboardMarkup(keyboard)

# تكملة النصوص للأزرار
TEXTS["ar"].update({
    "help_video": "🎬 تحميل فيديو",
    "help_audio": "🎵 استخراج صوت",
    "quality_menu": "⚡ اختيار الجودة",
    "share_bot": "🎁 مشاركة البوت",
    "my_stats": "📊 إحصائياتي",
    "help": "❓ المساعدة",
    "admin_panel": "👑 لوحة الأدمن",
    "admin_stats": "📊 إحصائيات البوت",
    "admin_top": "🏆 ترتيب المستخدمين",
    "admin_broadcast": "📢 إعلان للجميع",
    "admin_users": "👥 قائمة المستخدمين",
    "admin_block": "🚫 حظر مستخدم",
    "admin_unblock": "🔓 إلغاء حظر",
    "admin_clear": "🗑️ حذف الكاش",
    "admin_delete_all": "🗑️ حذف كل المستخدمين",
    "admin_uptime": "⏱️ وقت التشغيل",
    "admin_backup": "📤 نسخة احتياطية",
    "back": "🔙 رجوع",
    "audio": "🎵 صوت MP3"
})

TEXTS["en"].update({
    "help_video": "🎬 Download Video",
    "help_audio": "🎵 Extract Audio",
    "quality_menu": "⚡ Choose Quality",
    "share_bot": "🎁 Share Bot",
    "my_stats": "📊 My Stats",
    "help": "❓ Help",
    "admin_panel": "👑 Admin Panel",
    "admin_stats": "📊 Bot Stats",
    "admin_top": "🏆 Top Users",
    "admin_broadcast": "📢 Broadcast",
    "admin_users": "👥 Users List",
    "admin_block": "🚫 Block User",
    "admin_unblock": "🔓 Unblock User",
    "admin_clear": "🗑️ Clear Cache",
    "admin_delete_all": "🗑️ Delete All Users",
    "admin_uptime": "⏱️ Uptime",
    "admin_backup": "📤 Backup",
    "back": "🔙 Back",
    "audio": "🎵 MP3 Audio"
})

# ========== أوامر البوت ==========
async def start(update, context):
    u = update.effective_user
    text = update.message.text or ""
    lang = detect_language(text)
    
    if is_blocked(u.id):
        await update.message.reply_text(get_text("blocked", lang), parse_mode='Markdown')
        return
    
    save_user(u.id, u.username, context)
    
    welcome_text = f"""
🖤 *{get_text("welcome", lang).format(name=u.first_name)}* 🖤

✨ {SIGNATURE} ✨

📌 *{get_text("platforms", lang) if "platforms" in TEXTS.get(lang, {}) else "Supported platforms:"}* 
• TikTok • YouTube • Instagram
• Facebook • Twitter • SoundCloud
• Spotify • Deezer • And any website!

🎯 *{get_text("howto", lang) if "howto" in TEXTS.get(lang, {}) else "Just send any link and I'll download it"}*

{get_text("welcome", lang).format(name=u.first_name).split('🤍')[0]}🤍
"""
    kb = admin_keyboard(lang) if is_admin(u.id) else main_keyboard(lang)
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=kb)

async def privacy_cmd(update, context):
    u = update.effective_user
    text = update.message.text or ""
    lang = detect_language(text)
    
    privacy_text = f"""
🔒 *Privacy Policy*
━━━━━━━━━━━━━━━━━━━
📌 *Data we collect:*
• User ID
• Username
• First seen date
• Last seen date
• Download count

📅 *Data retention:*
• 30 days only
• Use /delete_my_data to delete

✨ {SIGNATURE} ✨
""" if lang == "en" else f"""
🔒 *سياسة الخصوصية*
━━━━━━━━━━━━━━━━━━━
📌 *البيانات التي نحتفظ بها:*
• معرف المستخدم
• اسم المستخدم
• تاريخ أول استخدام
• تاريخ آخر ظهور
• عدد التحميلات

📅 *مدة الاحتفاظ:*
• 30 يوم فقط
• استخدم /delete_my_data لحذف بياناتك

✨ {SIGNATURE} ✨
"""
    await update.message.reply_text(privacy_text, parse_mode='Markdown')

async def delete_my_data_cmd(update, context):
    u = update.effective_user
    text = update.message.text or ""
    lang = detect_language(text)
    
    if delete_user_data(u.id):
        await update.message.reply_text(get_text("deleted", lang).format(SIGNATURE=SIGNATURE), parse_mode='Markdown')
    else:
        await update.message.reply_text(get_text("not_found", lang), parse_mode='Markdown')

async def handle_message(update, context):
    u = update.effective_user
    msg_text = update.message.text or ""
    lang = detect_language(msg_text)
    
    if is_blocked(u.id):
        await update.message.reply_text(get_text("blocked", lang), parse_mode='Markdown')
        return
    
    url = extract_link(msg_text)
    
    if not url:
        await update.message.reply_text(get_text("no_link", lang), parse_mode='Markdown')
        return
    
    platform = get_platform(url)
    
    # ========== الخطوة 1: جلب معلومات الفيديو ==========
    step_msg = await update.message.reply_text(get_text("step1", lang).format(platform=platform), parse_mode='Markdown')
    
    video_info = await get_video_info(url)
    
    if video_info:
        info_text = f"""
📹 *Video Info*
━━━━━━━━━━━━━━━━━━━
📝 *Title:* {video_info['title'][:50]}
⏱️ *Duration:* {video_info['duration']}
📦 *Size:* {video_info['size']}
📱 *Platform:* {platform}
━━━━━━━━━━━━━━━━━━━
{get_text("confirm", lang)}
""" if lang == "en" else f"""
📹 *معلومات الفيديو*
━━━━━━━━━━━━━━━━━━━
📝 *العنوان:* {video_info['title'][:50]}
⏱️ *المدة:* {video_info['duration']}
📦 *الحجم:* {video_info['size']}
📱 *المنصة:* {platform}
━━━━━━━━━━━━━━━━━━━
{get_text("confirm", lang)}
"""
        await step_msg.edit_text(info_text, parse_mode='Markdown', reply_markup=confirm_keyboard(lang))
        context.user_data['pending_url'] = url
        context.user_data['pending_platform'] = platform
        context.user_data['pending_lang'] = lang
        return
    else:
        await step_msg.edit_text(get_text("step1", lang).format(platform=platform), parse_mode='Markdown')
        await asyncio.sleep(1)
    
    await perform_download(update, context, url, platform, lang)

async def confirm_callback(update, context):
    q = update.callback_query
    await q.answer()
    u = update.effective_user
    lang = context.user_data.get('pending_lang', 'ar')
    
    if q.data == "confirm_yes":
        url = context.user_data.get('pending_url')
        platform = context.user_data.get('pending_platform')
        await q.edit_message_text(get_text("confirm_yes", lang), parse_mode='Markdown')
        await perform_download(update, context, url, platform, lang)
    elif q.data == "confirm_no":
        await q.edit_message_text(get_text("confirm_no", lang), parse_mode='Markdown')
        context.user_data.pop('pending_url', None)
        context.user_data.pop('pending_platform', None)
        context.user_data.pop('pending_lang', None)

async def perform_download(update, context, url, platform, lang):
    u = update.effective_user
    quality = context.user_data.get('quality', '720')
    audio = context.user_data.get('audio', False)
    
    # ========== الخطوة 2: بدء التحميل ==========
    step_msg = await update.message.reply_text(get_text("step2", lang).format(platform=platform), parse_mode='Markdown')
    
    try:
        path, title = await download_media(url, quality, audio)
        size = os.path.getsize(path) / 1048576
        
        # ========== الخطوة 3: اكتمل التحميل ==========
        await step_msg.edit_text(get_text("step3", lang).format(size=f"{size:.1f}"), parse_mode='Markdown')
        
        # ========== الخطوة 4: إرسال الملف ==========
        if audio:
            with open(path, 'rb') as f:
                await update.message.reply_audio(
                    audio=f, 
                    title=title[:50], 
                    caption=f"{get_random_success_text(lang)}\n\n{SIGNATURE}", 
                    parse_mode='Markdown'
                )
        else:
            success_sticker = get_random_sticker("success")
            success_text = get_random_success_text(lang)
            with open(path, 'rb') as f:
                await update.message.reply_video(
                    f, 
                    caption=f"{success_sticker} {success_text}\n\n🎬 *{title[:60]}*\n📦 `{size:.1f} MB`\n⚡ `{quality}p`\n📱 `{platform}`\n\n{SIGNATURE}", 
                    parse_mode='Markdown', 
                    supports_streaming=True
                )
        
        os.remove(path)
        update_stats(u.id)
        await step_msg.delete()
    except Exception as e:
        error_text = get_random_error_text(lang)
        await step_msg.edit_text(f"{error_text}\n```\n{str(e)[:100]}\n```\n🔄 {get_text("error", lang)}", parse_mode='Markdown')

async def audio_cmd(update, context):
    u = update.effective_user
    text = update.message.text or ""
    lang = detect_language(text)
    
    if is_blocked(u.id):
        await update.message.reply_text(get_text("blocked", lang), parse_mode='Markdown')
        return
    
    context.user_data['audio'] = True
    audio_msg = "🎵 *Audio extraction mode activated*\nSend me a video link" if lang == "en" else "🎵 *وضع استخراج الصوت مفعل*\nأرسل رابط الفيديو"
    await update.message.reply_text(audio_msg, parse_mode='Markdown')

async def stats_cmd(update, context):
    u = update.effective_user
    text = update.message.text or ""
    lang = detect_language(text)
    
    if is_blocked(u.id):
        await update.message.reply_text(get_text("blocked", lang), parse_mode='Markdown')
        return
    
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    user_data = data['users'].get(str(u.id), {})
    
    stats_text = f"""📊 *Your Stats*
━━━━━━━━━━━━━━━━━━━
📥 *Downloads:* {user_data.get('downloads', 0)}

🌍 *Bot Stats*
━━━━━━━━━━━━━━━━━━━
📥 *Total:* {data['total']:,}
📈 *Today:* {data['daily']}

✨ {SIGNATURE} ✨
""" if lang == "en" else f"""📊 *إحصائياتك*
━━━━━━━━━━━━━━━━━━━
📥 *تحميلات:* {user_data.get('downloads', 0)}

🌍 *البوت*
━━━━━━━━━━━━━━━━━━━
📥 *إجمالي:* {data['total']:,}
📈 *اليوم:* {data['daily']}

✨ {SIGNATURE} ✨
"""
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def share_cmd(update, context):
    u = update.effective_user
    text = update.message.text or ""
    lang = detect_language(text)
    
    if is_blocked(u.id):
        await update.message.reply_text(get_text("blocked", lang), parse_mode='Markdown')
        return
    
    bot = await context.bot.get_me()
    link = f"https://t.me/{bot.username}"
    share_text = f"🎁 *Share Bot*\n`{link}`\n\n{SIGNATURE}" if lang == "en" else f"🎁 *شارك البوت*\n`{link}`\n\n{SIGNATURE}"
    await update.message.reply_text(share_text, parse_mode='Markdown')

async def top_cmd(update, context):
    u = update.effective_user
    text = update.message.text or ""
    lang = detect_language(text)
    
    if is_blocked(u.id):
        await update.message.reply_text(get_text("blocked", lang), parse_mode='Markdown')
        return
    
    top_users = get_top_users(10)
    if not top_users:
        await update.message.reply_text("🏆 *No users yet*" if lang == "en" else "🏆 *لا يوجد مستخدمين بعد*", parse_mode='Markdown')
        return
    
    header = "🏆 *Most Active Users* 🏆\n━━━━━━━━━━━━━━━━━━━\n" if lang == "en" else "🏆 *ترتيب المستخدمين الأكثر نشاطاً* 🏆\n━━━━━━━━━━━━━━━━━━━\n"
    text_msg = header
    for i, (uid, info) in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
        text_msg += f"{medal} *{info.get('name', 'Unknown')}* - 📥 {info.get('downloads', 0)} download{'s' if info.get('downloads', 0) != 1 else ''}\n"
    text_msg += f"\n✨ {SIGNATURE} ✨"
    await update.message.reply_text(text_msg, parse_mode='Markdown')

# ========== أوامر الأدمن ==========
async def admin_stats(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    blocked_count = sum(1 for u in data["users"].values() if u.get("blocked", False))
    text = f"""👑 *Bot Statistics* 👑
━━━━━━━━━━━━━━━━━━━
👥 *Users:* {len(data['users'])}
🚫 *Blocked:* {blocked_count}
📥 *Total Downloads:* {data['total']:,}
📈 *Today:* {data['daily']}

✨ {SIGNATURE} ✨
"""
    await update.message.reply_text(text, parse_mode='Markdown')

async def admin_top(update, context):
    if not is_admin(update.effective_user.id):
        return
    top_users = get_top_users(10)
    if not top_users:
        await update.message.reply_text("🏆 *No users yet*", parse_mode='Markdown')
        return
    
    text = "👑 *Top Active Users* 👑\n━━━━━━━━━━━━━━━━━━━\n"
    for i, (uid, info) in enumerate(top_users, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
        status = "🚫" if info.get("blocked", False) else "✅"
        text += f"{medal} `{uid}` - {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)}\n"
    text += f"\n✨ {SIGNATURE} ✨"
    await update.message.reply_text(text, parse_mode='Markdown')

async def broadcast_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("📢 /broadcast <message>")
        return
    s = await update.message.reply_text("🔄 Sending...")
    users = get_users()
    sent = 0
    failed = 0
    for uid in users:
        try:
            await context.bot.send_message(int(uid), f"📢 *Announcement* 📢\n━━━━━━━━━━━━━━━━━━━\n{msg}\n━━━━━━━━━━━━━━━━━━━\n{SIGNATURE}", parse_mode='Markdown')
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    await s.edit_text(f"✅ Sent\n📨 Success: {sent}\n❌ Failed: {failed}")

async def users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    txt = "👥 *Users List*\n━━━━━━━━━━━━━━━━━━━\n"
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
    await update.message.reply_text(f"🗑️ *Deleted {c} temporary files*\n\n{SIGNATURE}", parse_mode='Markdown')

async def delete_all_users_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    with open(DB_FILE, 'w') as f:
        json.dump({"users": {}, "total": 0, "daily": 0, "last_date": str(datetime.now().date())}, f, indent=2)
    await update.message.reply_text(f"🗑️ *All users deleted*\n\n{SIGNATURE}", parse_mode='Markdown')

async def uptime_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    uptime = get_uptime()
    await update.message.reply_text(f"⏱️ *Bot Uptime*\n━━━━━━━━━━━━━━━━━━━\n{uptime}\n━━━━━━━━━━━━━━━━━━━\n{SIGNATURE}", parse_mode='Markdown')

async def backup_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy(DB_FILE, backup_file)
    await update.message.reply_document(open(backup_file, 'rb'), caption=f"📦 *Backup*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{SIGNATURE}", parse_mode='Markdown')
    os.remove(backup_file)

async def block_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("🚫 /block <user_id>\nExample: `/block 123456789`")
        return
    user_id = context.args[0]
    if block_user(user_id):
        await update.message.reply_text(f"✅ *Blocked user* `{user_id}`\n\n{SIGNATURE}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ *User* `{user_id}` *not found*", parse_mode='Markdown')

async def unblock_user_cmd(update, context):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("🔓 /unblock <user_id>\nExample: `/unblock 123456789`")
        return
    user_id = context.args[0]
    if unblock_user(user_id):
        await update.message.reply_text(f"✅ *Unblocked user* `{user_id}`\n\n{SIGNATURE}", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ *User* `{user_id}` *not found*", parse_mode='Markdown')

# ========== معالجة الأزرار ==========
async def callback(update, context):
    q = update.callback_query
    await q.answer()
    u = update.effective_user.id
    lang = "en"  # سنحدد لاحقاً حسب اللغة المخزنة
    
    if q.data.startswith('q_'):
        val = q.data[2:]
        if val == 'audio':
            context.user_data['audio'] = True
            await q.edit_message_text("🎵 Audio mode activated" if lang == "en" else "🎵 وضع الصوت مفعل", parse_mode='Markdown')
        else:
            context.user_data['quality'] = val
            context.user_data['audio'] = False
            await q.edit_message_text(f"⚡ Quality set to {val}p", parse_mode='Markdown')
    
    elif q.data == 'quality_menu':
        await q.edit_message_text("⚡ *Choose quality:*" if lang == "en" else "⚡ *اختر الجودة:*", parse_mode='Markdown', reply_markup=quality_keyboard(lang))
    
    elif q.data == 'share_bot':
        bot = await context.bot.get_me()
        link = f"https://t.me/{bot.username}"
        await q.edit_message_text(f"🎁 *Bot link:*\n`{link}`\n\n{SIGNATURE}", parse_mode='Markdown')
    
    elif q.data == 'my_stats':
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        user_data = data['users'].get(str(u), {})
        text = f"📊 *Your Stats*\n━━━━━━━━━━━━━━━━━━━\n📥 Downloads: {user_data.get('downloads', 0)}\n\n🌍 Bot Total: {data['total']:,}\n📈 Today: {data['daily']}" if lang == "en" else f"📊 *إحصائياتك*\n━━━━━━━━━━━━━━━━━━━\n📥 تحميلات: {user_data.get('downloads', 0)}\n\n🌍 إجمالي البوت: {data['total']:,}\n📈 اليوم: {data['daily']}"
        await q.edit_message_text(text, parse_mode='Markdown')
    
    elif q.data == 'admin_panel':
        if is_admin(u):
            await q.edit_message_text("👑 *Admin Panel*", parse_mode='Markdown', reply_markup=admin_panel(lang))
        else:
            await q.edit_message_text("⛔ *Unauthorized*", parse_mode='Markdown')
    
    elif q.data == 'admin_stats':
        if not is_admin(u):
            return
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        blocked_count = sum(1 for user in data["users"].values() if user.get("blocked", False))
        text = f"👑 *Bot Stats*\n━━━━━━━━━━━━━━━━━━━\n👥 Users: {len(data['users'])}\n🚫 Blocked: {blocked_count}\n📥 Total: {data['total']:,}\n📈 Today: {data['daily']}"
        await q.edit_message_text(text, parse_mode='Markdown', reply_markup=admin_panel(lang))
    
    elif q.data == 'admin_top':
        if not is_admin(u):
            return
        top_users = get_top_users(10)
        if not top_users:
            await q.edit_message_text("🏆 No users yet", reply_markup=admin_panel(lang))
            return
        text = "👑 *Top Users* 👑\n━━━━━━━━━━━━━━━━━━━\n"
        for i, (uid, info) in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
            status = "🚫" if info.get("blocked", False) else "✅"
            text += f"{medal} {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)}\n"
        await q.edit_message_text(text, parse_mode='Markdown', reply_markup=admin_panel(lang))
    
    elif q.data == 'admin_broadcast':
        await q.edit_message_text("📢 *Send broadcast:*\n`/broadcast <message>`", parse_mode='Markdown', reply_markup=admin_panel(lang))
    
    elif q.data == 'admin_users':
        if not is_admin(u):
            return
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        txt = "👥 *Users List*\n━━━━━━━━━━━━━━━━━━━\n"
        for uid, info in list(data['users'].items())[:20]:
            status = "🚫" if info.get("blocked", False) else "✅"
            txt += f"• `{uid}` - {info.get('name', 'Unknown')} {status}\n   📥 {info.get('downloads', 0)}\n"
        await q.edit_message_text(txt, parse_mode='Markdown', reply_markup=admin_panel(lang))
    
    elif q.data == 'admin_block':
        await q.edit_message_text("🚫 *Block user:*\n`/block <user_id>`\n\nFind user_id with /users", parse_mode='Markdown', reply_markup=admin_panel(lang))
    
    elif q.data == 'admin_unblock':
        await q.edit_message_text("🔓 *Unblock user:*\n`/unblock <user_id>`\n\nFind user_id with /users", parse_mode='Markdown', reply_markup=admin_panel(lang))
    
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
        await q.edit_message_text(f"🗑️ *Deleted {c} files*", parse_mode='Markdown', reply_markup=admin_panel(lang))
    
    elif q.data == 'admin_delete_all':
        if not is_admin(u):
            return
        with open(DB_FILE, 'w') as f:
            json.dump({"users": {}, "total": 0, "daily": 0, "last_date": str(datetime.now().date())}, f, indent=2)
        await q.edit_message_text("🗑️ *All users deleted*", parse_mode='Markdown', reply_markup=admin_panel(lang))
    
    elif q.data == 'admin_uptime':
        if not is_admin(u):
            return
        uptime = get_uptime()
        await q.edit_message_text(f"⏱️ *Bot Uptime*\n━━━━━━━━━━━━━━━━━━━\n{uptime}", parse_mode='Markdown', reply_markup=admin_panel(lang))
    
    elif q.data == 'admin_backup':
        if not is_admin(u):
            return
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy(DB_FILE, backup_file)
        await q.message.reply_document(open(backup_file, 'rb'), caption=f"📦 *Backup*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{SIGNATURE}", parse_mode='Markdown')
        os.remove(backup_file)
        await q.edit_message_text("📤 *Backup sent*", parse_mode='Markdown', reply_markup=admin_panel(lang))
    
    elif q.data == 'help_video':
        await q.edit_message_text("🎬 *Download Video*\n━━━━━━━━━━━━━━━━━━━\n📤 Send me a video link and I'll download it\n\n✅ Works on all platforms", parse_mode='Markdown')
    
    elif q.data == 'help_audio':
        await q.edit_message_text("🎵 *Extract Audio*\n━━━━━━━━━━━━━━━━━━━\n📤 Use /audio then send a video link\n\n🎧 MP3 high quality", parse_mode='Markdown')
    
    elif q.data == 'help':
        help_text = """📌 *Help*
━━━━━━━━━━━━━━━━━━━
🎬 *Download:* Send link directly
🎵 *Audio:* /audio + link
⚡ *Quality:* Choose from menu
📊 *Stats:* /stats
🎁 *Share:* /share
🔒 *Privacy:* /privacy
🗑️ *Delete data:* /delete_my_data

✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨"""
        await q.edit_message_text(help_text, parse_mode='Markdown')
    
    elif q.data == 'back':
        kb = admin_keyboard(lang) if is_admin(u) else main_keyboard(lang)
        await q.edit_message_text("🖤 *Main Menu* 🖤", reply_markup=kb, parse_mode='Markdown')
    
    elif q.data == 'confirm_yes' or q.data == 'confirm_no':
        await confirm_callback(update, context)

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
    app.add_handler(CommandHandler("privacy", privacy_cmd))
    app.add_handler(CommandHandler("delete_my_data", delete_my_data_cmd))
    
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
    print("🌍 البوت العالمي النهائي شغال يا باشا!")
    print(f"👑 الأدمن: {ADMIN_IDS}")
    print(f"📦 الإصدار: {VERSION}")
    print("✅ بينزل أي حاجة من أي موقع")
    print("🌐 يدعم العربي والإنجليزي")
    print("=" * 60)
    app.run_polling()

if __name__ == "__main__":
    main()
