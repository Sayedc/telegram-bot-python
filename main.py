import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ابعت لينك وأنا أحملهولك 🔥")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        ydl_opts = {
            'outtmpl': 'file.%(ext)s',
            'format': 'best[filesize<50M]',
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await msg.delete()

        with open(filename, 'rb') as f:
            await update.message.reply_document(document=f)

        os.remove(filename)

    except Exception as e:
        await msg.delete()
        print(e)
        await update.message.reply_text("❌ حصل خطأ")

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, download))

print("Bot is running...")
app.run_polling()
