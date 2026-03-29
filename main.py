import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8137693278:AAEwPTeHj8JEwglERKzKvDdAAabAX1Gs08I"

# إنشاء فولدر التحميل لو مش موجود
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 ابعت لينك فيديو أو صورة (TikTok) وأنا أحمله لك")


async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    await update.message.reply_text("⏳ جاري التحميل...")

    try:
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # لو فيديو
            if 'ext' in info:
                file_path = ydl.prepare_filename(info)

                # لو صورة (TikTok Photo)
                if info.get("_type") == "playlist" or isinstance(info.get("entries"), list):
                    for entry in info['entries']:
                        file_path = ydl.prepare_filename(entry)
                        await update.message.reply_photo(photo=open(file_path, 'rb'))
                else:
                    await update.message.reply_video(video=open(file_path, 'rb'))

            else:
                await update.message.reply_text("❌ مش قادر أحدد نوع الملف")

    except Exception as e:
        await update.message.reply_text(f"❌ ERROR: {str(e)}")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
