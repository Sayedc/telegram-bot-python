import telebot
import yt_dlp
import os
import glob

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()

    # لو فيه لينك
    if "http" in text:
        bot.reply_to(message, "⏳ جاري تحميل الفيديو...")

        ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'best',
            'noplaylist': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)

            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video)

            os.remove(filename)

        except Exception as e:
            bot.reply_to(message, "❌ حصل خطأ أثناء التحميل")

    else:
        bot.reply_to(message, "ابعت لينك فيديو 🎥")

bot.infinity_polling()
