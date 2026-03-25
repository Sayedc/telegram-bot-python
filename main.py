import telebot
import yt_dlp
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text

    if "http" in text or "www" in text:
        bot.reply_to(message, "⏳ جاري تحميل الفيديو 🔥")

        ydl_opts = {
    'outtmpl': '%(title)s.%(ext)s',
    'format': 'best',
    'noplaylist': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            import glob

video_file = glob.glob("*.mp4")[0]

with open(video_file, "rb") as video:
                bot.send_video(message.chat.id, video)


        except Exception as e:
            bot.reply_to(message, "❌ حصل خطأ")

    else:
        bot.reply_to(message, "ابعت لينك فيديو 😏")
bot.infinity_polling()
