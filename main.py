import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

# فك اللينك المختصر
def expand_url(url):
    try:
        r = requests.get(url, allow_redirects=True)
        return r.url
    except:
        return url

# أوامر
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ازيك يا نجم!\n🔥 ابعتلي لينك TikTok وانا احملهولك")

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❤️ عامل ايه يا حبيبي؟")

# تحميل الفيديو
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "tiktok.com" not in url:
        await update.message.reply_text("❌ ده مش لينك TikTok")
        return

    await update.message.reply_text("⏳ جاري التحميل...")

    try:
        # نفك اللينك المختصر
        url = expand_url(url)

        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'mp4'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await update.message.reply_video(video=open("video.mp4", "rb"))

        os.remove("video.mp4")

    except Exception as e:
        await update.message.reply_text(f"❌ حصل خطأ:\n{e}")

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("hello", hello))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

app.run_polling()
