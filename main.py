import os
import re
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

from config import BOT_TOKEN, ADMIN_IDS, MAX_FILE_SIZE_MB, DOWNLOADS_PATH

# ========== إعداد المسارات ==========
os.makedirs(DOWNLOADS_PATH, exist_ok=True)

# ========== قاعدة بيانات بسيطة ==========
DB_FILE = "bot_database.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({"users": {}, "stats": {"total_downloads": 0}}, f)

def save_user(user_id, username):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {"username": username, "downloads": 0}
            f.seek(0)
            json.dump(data, f)

def update_stats(user_id):
    with open(DB_FILE, 'r+') as f:
        data = json.load(f)
        if str(user_id) in data["users"]:
            data["users"][str(user_id)]["downloads"] += 1
            data["stats"]["total_downloads"] += 1
            f.seek(0)
            json.dump(data, f)

# ========== استخراج الرابط ==========
def extract_link(text: str):
    match = re.search(r'(https?://[^\s]+)', text)
    return match.group(0) if match else None

# ========== التحميل باستخدام yt-dlp ==========
async def download_media(url, audio_only=False):
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
        ydl_opts['format'] = 'best'

    # إزالة علامة تيك توك المائية
    if 'tiktok.com' in url:
        ydl_opts['extractor_args'] = {'tiktok': {'without_watermark': ['true']}}

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
    await update.message.reply_text(
        f"🎬 مرحباً {user.first_name}!\n\nأرسل رابط فيديو/صورة من:\nYouTube - Instagram - TikTok - Facebook - Twitter\nوسأقوم بتحميله لك فوراً ✅"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = extract_link(update.message.text)

    if not url:
        await update.message.reply_text("❌ لم أجد رابطاً صالحاً. أرسل رابط فيديو أو منشور.")
        return

    status = await update.message.reply_text("🔄 جاري التحميل...")

    try:
        # تحميل فيديو عادي
        file_path, title = await download_media(url, audio_only=False)

        # إرسال الملف
        with open(file_path, 'rb') as f:
            await update.message.reply_video(video=f, caption=f"✅ {title[:60]}", supports_streaming=True)

        os.remove(file_path)
        update_stats(user_id)
        await status.delete()

    except Exception as e:
        await status.edit_text(f"❌ فشل التحميل: {str(e)[:100]}")

async def audio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['audio_mode'] = True
    await update.message.reply_text("🎵 أرسل رابط الفيديو لاستخراج الصوت MP3")

# ========== التشغيل الرئيسي ==========
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("audio", audio_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
