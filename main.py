# main.py
import os
import re
import json
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

from config import BOT_TOKEN, ADMIN_IDS, MAX_FILE_SIZE_MB, DOWNLOADS_PATH

# ========== إعداد المسارات ==========
os.makedirs(DOWNLOADS_PATH, exist_ok=True)

# ========== التوقيع الفاخر ==========
SIGNATURE = "✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨"

# ========== ردود مصرية ==========
EGYPTIAN_RESPONSES = {
    "welcome": [
        "🎬 اهلاً بيك يا باشا {name}! نورت البوت 🤍",
        "💫 أهلاً وسهلاً يا فنان {name}! تسلملي 🌟",
        "🔥 يا مرحبا بيك يا كبير {name}! البوت تحت أمرك 😎",
    ],
    "processing": [
        "⚡ شوية صبر يا حبيب قلبى، البوت بيشتغل... 🎬",
        "🔥 على توكل على الله، جاري التحميل يا كبير... 💫",
        "🎯 معلش سيبني اشتغل شوية، النتيجة هتعجبك بإذن الله ✨",
    ],
    "success": [
        "✅ تم يا فنان! تسلملي 🌟\n{SIGNATURE}",
        "🎬 خد الفيديو يا باشا، ألف هنا 🤍\n{SIGNATURE}",
        "🔥 تم التحميل يا حبيبى، استلم وخلاص 😎\n{SIGNATURE}",
    ],
    "audio_success": [
        "🎵 خد الصوت يا فنان، عقبال ما تسمعه 🤍\n{SIGNATURE}",
        "🎧 تسلم يا كبير، الصوت جاهز 🌟\n{SIGNATURE}",
    ],
    "no_link": [
        "❌ يا باشا، انت نسيت ترسل الرابط! 😅\n📌 أرسل رابط فيديو من يوتيوب، تيك توك، إنستا، أو فيسبوك",
        "🤔 معلش يا حبى، أنا مش شايف أي رابط في رسالتك...\n⚡ جرب تبعت الرابط لوحده بلا كلام",
    ],
    "error": [
        "❌ معلش يا باشا، حصلت مشكلة في التحميل 😅\n🔄 جرب تاني حبه، أو غير الرابط",
        "🔥 البوت وقع في حوار صغير، جرب تاني يا كبير 💫",
    ],
    "admin_only": [
        "👑 يا باشا، الأمر ده للأدمن بس! 😅\nإنت مش الرئيس يعنى 🫢",
    ],
}

def get_random_response(key, name=None):
    responses = EGYPTIAN_RESPONSES.get(key, ["تم"])
    text = responses[datetime.now().second % len(responses)]
    if name:
        text = text.format(name=name)
    return text

# ========== قاعدة بيانات ==========
DB_FILE = "bot_database.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"users": {}, "stats": {"total_downloads": 0}}, f, indent=2)

def save_user(user_id, username):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {
                "username": username,
                "first_seen": datetime.now().isoformat(),
                "downloads": 0,
                "blocked": False
            }
            f.seek(0)
            json.dump(data, f, indent=2)

def update_stats(user_id):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["downloads"] += 1
            data["stats"]["total_downloads"] += 1
            f.seek(0)
            json.dump(data, f, indent=2)

def get_all_users():
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
        return [uid for uid, u in data["users"].items() if not u.get("blocked", False)]

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ========== أزرار فخمة ==========
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 ✦ تحميل فيديو ✦", callback_data="help_video"),
         InlineKeyboardButton("🎵 ✦ استخراج صوت ✦", callback_data="help_audio")],
        [InlineKeyboardButton("⚡ ✦ اختيار الجودة ✦", callback_data="quality_menu"),
         InlineKeyboardButton("📊 ✦ إحصائياتي ✦", callback_data="my_stats")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 ✦ لوحة التحكم ✦", callback_data="admin_panel")],
        [InlineKeyboardButton("🎬 ✦ تحميل فيديو ✦", callback_data="help_video"),
         InlineKeyboardButton("🎵 ✦ استخراج صوت ✦", callback_data="help_audio")],
        [InlineKeyboardButton("⚡ ✦ اختيار الجودة ✦", callback_data="quality_menu"),
         InlineKeyboardButton("📊 ✦ إحصائياتي ✦", callback_data="my_stats")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_panel():
    keyboard = [
        [InlineKeyboardButton("📊 ✦ إحصائيات البوت ✦", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 ✦ إعلان للجميع ✦", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 ✦ قائمة المستخدمين ✦", callback_data="admin_users")],
        [InlineKeyboardButton("🗑️ ✦ حذف الكاش ✦", callback_data="admin_clear")],
        [InlineKeyboardButton("🔙 ✦ رجوع ✦", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quality_keyboard():
    keyboard = [
        [InlineKeyboardButton("📱 144p", callback_data="quality_144"),
         InlineKeyboardButton("📱 240p", callback_data="quality_240"),
         InlineKeyboardButton("📱 360p", callback_data="quality_360")],
        [InlineKeyboardButton("📺 480p", callback_data="quality_480"),
         InlineKeyboardButton("📺 720p 🔥", callback_data="quality_720"),
         InlineKeyboardButton("📺 1080p 👑", callback_data="quality_1080")],
        [InlineKeyboardButton("🎵 ✦ صوت فقط MP3 ✦", callback_data="quality_audio")],
        [InlineKeyboardButton("🔙 ✦ رجوع ✦", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== استخراج الرابط من وسط الكلام ==========
def extract_link(text: str):
    patterns = [
        r'(https?://(?:www\.)?tiktok\.com/[^\s]+)',
        r'(https?://vt\.tiktok\.com/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/watch\?v=[^\s&]+)',
        r'(https?://youtu\.be/[^\s]+)',
        r'(https?://(?:www\.)?instagram\.com/(?:p|reel|stories)/[^\s/?]+)',
        r'(https?://(?:www\.)?facebook\.com/(?:watch|reel|share[v]?)/[^\s]+)',
        r'(https?://(?:www\.)?fb\.watch/[^\s]+)',
        r'(https?://(?:www\.)?twitter\.com/[\w]+/status/[\d]+)',
        r'(https?://(?:www\.)?x\.com/[\w]+/status/[\d]+)',
        r'(https?://[^\s]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

# ========== تحميل تيك توك بدون علامة مائية ==========
async def download_tiktok(url):
    ydl_opts = {
        'outtmpl': f'{DOWNLOADS_PATH}/tiktok_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'extractor_args': {
            'tiktok': {
                'without_watermark': ['true'],
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        return file_path, info.get('title', 'TikTok Video')

# ========== تحميل عام مع جودة ==========
async def download_media(url, quality=None, audio_only=False):
    if 'tiktok.com' in url or 'vt.tiktok.com' in url:
        return await download_tiktok(url)
    
    quality_map = {
        '144': 'worst[height<=144]',
        '240': 'best[height<=240]',
        '360': 'best[height<=360]',
        '480': 'best[height<=480]',
        '720': 'best[height<=720]',
        '1080': 'best[height<=1080]',
    }
    
    if audio_only:
        ydl_opts = {
            'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        }
    else:
        format_str = quality_map.get(quality, 'best[height<=720]')
        ydl_opts = {
            'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'format': format_str,
        }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        if audio_only:
            file_path = file_path.rsplit('.', 1)[0] + '.mp3'
        return file_path, info.get('title', 'Media')

# ========== أوامر البوت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username)
    
    text = f"""
🖤 *البوت الأسود الفاخر* 🖤
✨ 𝓐𝓵𝓱𝓪𝔀𝔂 𝓐𝓲 𝓑𝓸𝓽 ✨

🔥 *أهلاً بيك يا باشا* {user.first_name}!

🎯 *أنا البوت اللي هيسهل عليك الدنيا*

📥 *المنصات اللي بشتغل عليها:*
✦ TikTok 🎵 (بدون علامة مائية)
✦ YouTube 🎬
✦ Instagram 📸
✦ Facebook 📘
✦ Twitter 🐦

💫 *مميزاتي الخارقة:*
✅ اختار جودة التحميل بنفسك
✅ استخراج صوت MP3 بجودة عالية
✅ سرعة فائقة في التحميل
✅ مفيش إعلانات ولا حاجة

⚡ *ابعتلي الرابط وأنا هخلص الباقي*
{get_random_response('welcome', user.first_name)}
"""
    if is_admin(user.id):
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    message_text = update.message.text
    
    url = extract_link(message_text)
    quality = context.user_data.get('preferred_quality', '720')
    audio_mode = context.user_data.get('audio_mode', False)
    
    if not url:
        await update.message.reply_text(get_random_response('no_link'), parse_mode='Markdown')
        return
    
    # رسالة جاري المعالجة
    status_msg = await update.message.reply_text(
        f"✨ {get_random_response('processing', user_name)}\n⚡ الرابط: `{url[:50]}...`",
        parse_mode='Markdown'
    )
    
    try:
        file_path, title = await download_media(url, quality=quality, audio_only=audio_mode)
        
        if audio_mode:
            with open(file_path, 'rb') as f:
                await update.message.reply_audio(
                    audio=f,
                    title=title[:50],
                    caption=f"🎵 {get_random_response('audio_success', user_name)}",
                    parse_mode='Markdown'
                )
            context.user_data['audio_mode'] = False
        else:
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            with open(file_path, 'rb') as f:
                await update.message.reply_video(
                    video=f,
                    caption=f"🎬 *{title[:60]}*\n━━━━━━━━━━━━━━━━━━━\n📦 الحجم: `{file_size:.1f} MB`\n⚡ الجودة: `{quality}p`\n━━━━━━━━━━━━━━━━━━━\n{get_random_response('success', user_name)}",
                    parse_mode='Markdown',
                    supports_streaming=True
                )
        
        os.remove(file_path)
        update_stats(user_id)
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(
            f"{get_random_response('error')}\n```\n{str(e)[:100]}\n```",
            parse_mode='Markdown'
        )

async def audio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['audio_mode'] = True
    await update.message.reply_text(
        "🎵 *وضع استخراج الصوت مفعل*\n\n📤 ابعتلي رابط الفيديو وهاخدلك الصوت MP3 بجودة عالية",
        parse_mode='Markdown'
    )

async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    
    user_data = data["users"].get(str(user_id), {})
    downloads = user_data.get('downloads', 0)
    quality = context.user_data.get('preferred_quality', '720')
    
    text = f"""
🖤 *إحصائيات {user_name}* 🖤
━━━━━━━━━━━━━━━━━━━
📥 *عدد التحميلات:* `{downloads}`
⚡ *الجودة المفضلة:* `{quality}p`
━━━━━━━━━━━━━━━━━━━
🌍 *إجمالي تحميلات البوت:* `{data['stats']['total_downloads']}`
━━━━━━━━━━━━━━━━━━━
✨ {SIGNATURE} ✨
"""
    await update.message.reply_text(text, parse_mode='Markdown')

# ========== أوامر الأدمن ==========
async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(get_random_response('admin_only'), parse_mode='Markdown')
        return
    
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    
    users = data['users']
    blocked = sum(1 for u in users.values() if u.get('blocked', False))
    
    text = f"""
👑 *لوحة تحكم الأدمن* 👑
━━━━━━━━━━━━━━━━━━━
👥 *المستخدمين:* `{len(users)}`
🚫 *محظورين:* `{blocked}`
📥 *إجمالي التحميلات:* `{data['stats']['total_downloads']}`
━━━━━━━━━━━━━━━━━━━
✨ {SIGNATURE} ✨
"""
    await update.message.reply_text(text, parse_mode='Markdown')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(get_random_response('admin_only'), parse_mode='Markdown')
        return
    
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("📢 *استخدم:* `/broadcast رسالتك`", parse_mode='Markdown')
        return
    
    status = await update.message.reply_text("🔄 جاري الإرسال للجميع...")
    users = get_all_users()
    sent = 0
    failed = 0
    
    for uid in users:
        try:
            await context.bot.send_message(
                int(uid),
                f"📢 *إعلان من الأدمن* 📢\n━━━━━━━━━━━━━━━━━━━\n{msg}\n━━━━━━━━━━━━━━━━━━━\n✨ {SIGNATURE} ✨",
                parse_mode='Markdown'
            )
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await status.edit_text(f"✅ تم الإرسال\n📨 نجح: `{sent}`\n❌ فشل: `{failed}`", parse_mode='Markdown')

async def admin_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    
    user_list = ""
    for uid, info in list(data['users'].items())[:30]:
        user_list += f"👤 `{uid}` - {info.get('username', 'Unknown')} - 📥 {info.get('downloads', 0)}\n"
    
    if not user_list:
        user_list = "لا يوجد مستخدمين"
    
    text = f"👥 *آخر 30 مستخدم*\n━━━━━━━━━━━━━━━━━━━\n{user_list}"
    await update.message.reply_text(text, parse_mode='Markdown')

async def clear_cache_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    
    count = 0
    for f in os.listdir(DOWNLOADS_PATH):
        f_path = os.path.join(DOWNLOADS_PATH, f)
        try:
            os.remove(f_path)
            count += 1
        except:
            pass
    
    await update.message.reply_text(f"🗑️ *تم حذف {count} ملف مؤقت*", parse_mode='Markdown')

# ========== معالجة الأزرار ==========
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    
    # أزرار الجودة
    if query.data.startswith("quality_"):
        q = query.data.replace("quality_", "")
        if q == "audio":
            context.user_data['audio_mode'] = True
            await query.edit_message_text("🎵 *وضع استخراج الصوت مفعل*\n📤 أرسل رابط الفيديو الآن", parse_mode='Markdown')
        else:
            context.user_data['preferred_quality'] = q
            await query.edit_message_text(f"⚡ *تم ضبط الجودة على {q}p*\n📥 أرسل الرابط الآن", parse_mode='Markdown')
    
    elif query.data == "quality_menu":
        await query.edit_message_text("⚡ *اختر جودة التحميل:*", parse_mode='Markdown', reply_markup=get_quality_keyboard())
    
    elif query.data == "my_stats":
        await my_stats(update, context)
    
    elif query.data == "admin_panel":
        if is_admin(user_id):
            await query.edit_message_text("👑 *لوحة تحكم الأدمن*", parse_mode='Markdown', reply_markup=get_admin_panel())
        else:
            await query.edit_message_text(get_random_response('admin_only'), parse_mode='Markdown')
    
    elif query.data == "admin_stats":
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        text = f"👑 *إحصائيات البوت*\n━━━━━━━━━━━\n👥 مستخدمين: {len(data['users'])}\n📥 تحميلات: {data['stats']['total_downloads']}"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_admin_panel())
    
    elif query.data == "admin_broadcast":
        await query.edit_message_text("📢 *أرسل رسالتك باستخدام:*\n`/broadcast الرسالة`", parse_mode='Markdown')
    
    elif query.data == "admin_users":
        await admin_users_command(update, context)
    
    elif query.data == "admin_clear":
        await clear_cache_command(update, context)
    
    elif query.data == "back_to_main":
        if is_admin(user_id):
            await query.edit_message_text("🖤 *القائمة الرئيسية*", parse_mode='Markdown', reply_markup=get_admin_keyboard())
        else:
            await query.edit_message_text("🖤 *القائمة الرئيسية*", parse_mode='Markdown', reply_markup=get_main_keyboard())
    
    elif query.data == "help_video":
        await query.edit_message_text("🎬 *أرسل رابط الفيديو وسأقوم بتحميله فوراً*", parse_mode='Markdown')
    
    elif query.data == "help_audio":
        await query.edit_message_text("🎵 *استخدم الأمر `/audio` ثم أرسل رابط الفيديو*", parse_mode='Markdown')

# ========== التشغيل ==========
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    # أوامر البوت
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", audio_command))
    app.add_handler(CommandHandler("stats", my_stats))
    app.add_handler(CommandHandler("adminstats", admin_stats_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # معالجة الرسائل والأزرار
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("=" * 50)
    print("✨ 𝓐𝓵𝓱𝓪𝔀𝔂 𝓐𝓲 𝓑𝓸𝓽 ✨")
    print("🔥 البوت الفاخر شغال يا باشا...")
    print(f"👑 الأدمن ID: {ADMIN_IDS}")
    print("=" * 50)
    app.run_polling()

if __name__ == "__main__":
    main()
