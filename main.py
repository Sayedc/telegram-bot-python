import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً 👋 ابعت لينك وأنا أحمله لك")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 ابعت:\nmp3 + لينك\nأو لينك بس للفيديو")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text.startswith("mp3"):
        url = text.replace("mp3", "").strip()
        await update.message.reply_text("⏳ جاري استخراج الصوت...")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "audio.%(ext)s",
            "noplaylist": True,
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            await update.message.reply_audio(open("audio.mp3", "rb"))

        except Exception as e:
            await update.message.reply_text(f"❌ حصل خطأ:\n{e}")

    else:
        url = text.strip()
        await update.message.reply_text("⏳ جاري تحميل الفيديو...")

        ydl_opts = {
            "format": "mp4[height<=720]/best",
            "outtmpl": "video.%(ext)s",
            "noplaylist": True,
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            await update.message.reply_video(open("video.mp4", "rb"))

        except Exception as e:
            await update.message.reply_text(f"❌ حصل خطأ:\n{e}")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
