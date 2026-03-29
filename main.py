import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

BOT_TOKEN = "8137693278:AAEwPTeHj8JEwglERKzKvDdAAabAX1Gs08I"

# إنشاء فولدر التحميل
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# رسالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 ابعتلي لينك فيديو أو صورة وأنا أحملهولك 😎")

# التحميل
def download(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

        return file_path

# استقبال اللينك
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "http" not in url:
        await update.message.reply_text("❌ ابعت لينك بس")
        return

    msg = await update.message.reply_text("⏳ بحمل... استنى شوية")

    try:
        file_path = download(url)

        # تحديد النوع
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            with open(file_path, 'rb') as f:
                await update.message.reply_photo(photo=f)
        else:
            with open(file_path, 'rb') as f:
                await update.message.reply_video(video=f)

        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"❌ حصلت مشكلة:\n{e}")

# تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()
