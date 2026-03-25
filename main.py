import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 📥 تحميل فيديو
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text.startswith("mp3"):
        url = text.replace("mp3", "").strip()

        await update.message.reply_text("⏳ جاري استخراج الصوت...")

        ydl_opts = {
            'format': 'best',
            'outtmpl': 'audio.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        for file in os.listdir():
            if file.endswith(".mp3"):
                with open(file, "rb") as audio:
                    await update.message.reply_audio(audio)
                os.remove(file)
                break

    else:
        url = text.strip()

        await update.message.reply_text("⏳ جاري تحميل الفيديو...")

        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.%(ext)s',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        for file in os.listdir():
            if file.startswith("video"):
                with open(file, "rb") as video:
                    await update.message.reply_video(video)
                os.remove(file)
                break


# 🚀 تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

print("Bot is running...")
app.run_polling()
