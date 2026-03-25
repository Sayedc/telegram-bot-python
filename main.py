import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ازيك يا نجم!\nابعت أي لينك من السوشيال وأنا أحملهولك 🔥")

# تحميل
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        ydl_opts = {
            'outtmpl': 'file.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # حذف رسالة التحميل
        await msg.delete()

        # إرسال الفيديو أو الملف
        if filename.endswith((".mp4", ".mkv", ".webm")):
            with open(filename, 'rb') as f:
                await update.message.reply_video(video=f)
        else:
            with open(filename, 'rb') as f:
                await update.message.reply_document(document=f)

        # رسالة ختامية
        await update.message.reply_text("🔥 الفيديو وصل يا نجم!")

        # حذف الملف
        os.remove(filename)

    except Exception as e:
        await msg.delete()
        print(e)
        await update.message.reply_text("❌ اللينك غلط أو مش مدعوم جرب غيره")

# تشغيل البوت
app = Application.builder().token(TOKEN).build()

app.add_handler(Command
