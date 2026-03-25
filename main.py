import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ابعت أي لينك من السوشيال وأنا أحمله لك بدون علامة مائية 😎🔥")

# تحميل
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("جاري التحميل ⏳")

    try:
        ydl_opts = {
            'outtmpl': 'file.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # لو فيديو
        if filename.endswith((".mp4", ".mkv", ".webm")):
            await update.message.reply_video(video=open(filename, 'rb'))
        else:
            await update.message.reply_document(document=open(filename, 'rb'))

        os.remove(filename)

    except Exception as e:
        await update.message.reply_text("مش عرفت أحمله 😢 جرب لينك تاني")

# تشغيل
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, download))

app.run_polling()
