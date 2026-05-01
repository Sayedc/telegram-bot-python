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
                "downloads": 0
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
        return list(data["users"].keys())

# ========== استخراج الرابط ==========
def extract_link(text: str):
    patterns = [
        r'(https?://(?:www\.)?tiktok\.com/[^\s]+)',
        r'(https?://vt\.tiktok\.com/[^\s]+)',
        r'(https?://(?:www\.)?youtube\.com/watch\?v=[^\s]+)',
        r'(https?://youtu\.be/[^\s]+)',
        r'(https?://(?:www\.)?instagram\.com/(?:p|reel|stories)/[^\s]+)',
        r'(https?://(?:www\.)?facebook\.com/(?:watch|reel)/[^\s]+)',
        r'(https?://(?:www\.)?twitter\.com/[\w]+/status/[\d]+)',
        r'(https?://[^\s]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
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

# ========== تحميل عام ==========
async def download_media(url, audio_only=False):
    # تيك توك معاملة خاصة
    if 'tiktok.com' in url or 'vt.tiktok.com' in url:
        return await download_tiktok(url)
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOADS_PATH}/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    if audio_only:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        })
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'
    
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
    
    text = f"""🎬 *مرحباً بك يا بطل* {user.first_name}! 🎬

✨ *أنا بوت تحميل الوسائط الذكي*

📥 *أرسل لي أي رابط من:*
• TikTok 🎵 (بدون علامة مائية)
• YouTube 🎬
• Instagram 📸
• Facebook 📘
• Twitter 🐦

🚀 *سأقوم بتحميله لك فوراً وبأعلى جودة!*

💡 *للأصوات فقط:* استخدم الأمر /audio
"""
    await update.message.reply_text(text, parse_mode='Markdown')

async def audio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['audio_mode'] = True
    await update.message.reply_text("🎵 *وضع استخراج الصوت مفعل*\nأرسل رابط الفيديو الآن وسأرسل لك MP3", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = extract_link(update.message.text)
    
    audio_mode = context.user_data.get('audio_mode', False)
    if audio_mode:
        context.user_data['audio_mode'] = False
    
    if not url:
        await update.message.reply_text("❌ *لم أجد رابطاً صالحاً*\nتأكد أن الرابط من TikTok أو YouTube أو Instagram أو Facebook", parse_mode='Markdown')
        return
    
    status_msg = await update.message.reply_text("🔄 *جاري التحميل...*\n⏱️ يرجى الانتظار", parse_mode='Markdown')
    
    try:
        file_path, title = await download_media(url, audio_only=audio_mode)
        
        if audio_mode:
            with open(file_path, 'rb') as f:
                await update.message.reply_audio(audio=f, title=title[:50], caption=f"✅ {title[:40]}")
        else:
            with open(file_path, 'rb') as f:
                await update.message.reply_video(video=f, caption=f"✅ *تم التحميل!*\n🎬 {title[:50]}", parse_mode='Markdown', supports_streaming=True)
        
        os.remove(file_path)
        update_stats(user_id)
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(f"❌ *فشل التحميل*\n```\n{str(e)[:150]}\n```\nحاول مرة أخرى", parse_mode='Markdown')

async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    
    user_data = data["users"].get(str(user_id), {})
    text = f"""📊 *إحصائياتك*\n📥 تحميلاتك: {user_data.get('downloads', 0)}\n🌍 إجمالي التحميلات: {data['stats']['total_downloads']}"""
    await update.message.reply_text(text, parse_mode='Markdown')

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ غير مصرح")
        return
    
    with open(DB_FILE, 'r') as f:
        data = json.load(f)
    
    text = f"""👑 *لوحة التحكم*\n👥 المستخدمين: {len(data['users'])}\n📥 التحميلات: {data['stats']['total_downloads']}"""
    await update.message.reply_text(text, parse_mode='Markdown')

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    msg = ' '.join(context.args)
    if not msg:
        await update.message.reply_text("📢 /broadcast <الرسالة>")
        return
    
    users = get_all_users()
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(int(uid), f"📢 *اعلان:*\n\n{msg}", parse_mode='Markdown')
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    await update.message.reply_text(f"✅ تم الإرسال لـ {sent} مستخدم")

# ========== التشغيل ==========
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", audio_command))
    app.add_handler(CommandHandler("stats", my_stats))
    app.add_handler(CommandHandler("adminstats", admin_stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ البوت شغال...")
    print(f"👑 الأدمن ID: {ADMIN_IDS}")
    app.run_polling()

if __name__ == "__main__":
    main()
