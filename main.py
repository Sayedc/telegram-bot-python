import re
import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# استخراج اللينك من الكلام
def extract_url(text):
    url_pattern = r"(https?://[^\s]+)"
    match = re.search(url_pattern, text)
    return match.group(0) if match else None

# تحديد نوع الموقع
def detect_platform(url):
    if "tiktok.com" in url:
        return "tiktok"
    elif "instagram.com" in url:
        return "instagram"
    elif "facebook.com" in url or "fb.watch" in url:
        return "facebook"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "other"

# زرار الجودة
def quality_buttons(url):
    keyboard = [
        [InlineKeyboardButton("⚡ 360p", callback_data=f"360|{url}")],
        [InlineKeyboardButton("🔥 720p", callback_data=f"720|{url}")],
        [InlineKeyboardButton("💎 HD", callback_data=f"best|{url}")],
        [InlineKeyboardButton("🎧 صوت فقط", callback_data=f"audio|{url}")]
    ]
    return InlineKeyboardMarkup(keyboard)

# أمر start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 ابعتلي أي لينك فيديو وأنا أحملهولك")

# استقبال الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    url = extract_url(text)

    if not url:
        await update.message.reply_text("❌ ابعت لينك صحيح")
        return

    await update.message.reply_text("🎬 اختر الجودة:", reply_markup=quality_buttons(url))

# تحميل الفيديو
def download_video(url, quality, platform):
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
        'ignoreerrors': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    }

    # حل مشاكل فيسبوك وانستا
    if platform in ["facebook", "instagram"]:
        ydl_opts['cookiefile'] = 'cookies.txt'

    # إزالة watermark من تيك توك
    if platform == "tiktok":
        ydl_opts['format'] = "best"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except:
        # fallback
        ydl_opts['format'] = "best"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

# التعامل مع الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    quality = data[0]
    url = data[1]

    platform = detect_platform(url)

    msg = await query.message.reply_text("⏳ جاري التحميل...")

    try:
        file_path = download_video(url, quality, platform)

        if quality == "audio":
            await query.message.reply_audio(audio=open(file_path, "rb"))
        else:
            await query.message.reply_video(video=open(file_path, "rb"))

        await msg.delete()

        os.remove(file_path)

    except Exception as e:
        await msg.edit_text("❌ حصل خطأ")

# تشغيل البوت
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await msg.delete()

        with open(filename, 'rb') as f:
            if file_type == "audio":
                await query.message.reply_audio(f)
            else:
                await query.message.reply_document(f)

        os.remove(filename)

        await query.message.reply_text("🔥 تم التحميل!")

    except Exception as e:
        print(e)
        await msg.delete()
        await query.message.reply_text("❌ حصل خطأ")

# تشغيل البوت
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(choose_type, pattern="^(video|audio)$"))
app.add_handler(CallbackQueryHandler(choose_quality, pattern="^(360|720|hd)$"))

print("Bot is running...")
app.run_polling()
