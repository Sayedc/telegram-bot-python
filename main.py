import re
import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN مش موجود!")
    exit()

print("✅ BOT TOKEN OK")

# استخراج اللينك من الكلام
def extract_url(text):
    match = re.search(r"(https?://[^\s]+)", text)
    return match.group(0) if match else None

# أزرار الجودة
def quality_buttons(url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ 360p", callback_data=f"360|{url}")],
        [InlineKeyboardButton("🔥 720p", callback_data=f"720|{url}")],
        [InlineKeyboardButton("💎 HD", callback_data=f"best|{url}")],
        [InlineKeyboardButton("🎧 صوت فقط", callback_data=f"audio|{url}")]
    ])

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📩 /start")
    await update.message.reply_text("🔥 ابعت لينك الفيديو")

# استقبال الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    url = extract_url(text)

    if not url:
        await update.message.reply_text("❌ ابعت لينك صحيح")
        return

    await update.message.reply_text("🎬 اختار الجودة:", reply_markup=quality_buttons(url))

# تحميل الفيديو
def download_video(url, quality):
    if quality == "360":
        fmt = "bestvideo[height<=360]+bestaudio/best[height<=360]"
    elif quality == "720":
        fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif quality == "audio":
        fmt = "bestaudio"
    else:
        fmt = "best"

    ydl_opts = {
        'format': fmt,
        'outtmpl': 'video.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'retries': 5,
        'fragment_retries': 5,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except:
        # fallback لو الجودة فشلت
        ydl_opts['format'] = "best"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

# التعامل مع الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quality, url = query.data.split("|")

    msg = await query.message.reply_text("⏳ جاري التحميل...")

    try:
        file_path = download_video(url, quality)

        if quality == "audio":
            await query.message.reply_audio(audio=open(file_path, "rb"))
        else:
            await query.message.reply_video(video=open(file_path, "rb"))

        await msg.delete()

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        print("ERROR:", e)
        await msg.edit_text("❌ حصل خطأ")

# تشغيل البوت
def main():
    print("🚀 Bot is running...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

# أهم سطر (التفعيل)
if __name__ == "__main__":
    main()

print("Bot is running...")
app.run_polling()
