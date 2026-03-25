import telebot
import yt_dlp
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text

    if "http" in text:
        bot.reply_to(message, "جاري تحميل الفيديو 🔥")

        ydl_opts = {
            'outtmpl': 'video.mp4',
            'format': 'best'
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            with open("video.mp4", "rb") as video:
                bot.send_video(message.chat.id, video)

        except:
            bot.reply_to(message, "حصل خطأ ❌")

    else:
        bot.reply_to(message, "ابعت لينك فيديو 😎")

bot.infinity_polling()
