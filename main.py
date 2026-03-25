import os
import telebot
import yt_dlp
import time

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ TOKEN مش موجود")
    exit()

bot = telebot.TeleBot(TOKEN)

# منع السبام
users = {}

def can_download(user_id):
    now = time.time()
    if user_id in users:
        if now - users[user_id] < 5:
            return False
    users[user_id] = now
    return True

# /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
        "🔥 أهلاً بيك في بوت تحميل الفيديوهات\n\n"
        "📌 ابعت لينك فيديو وأنا أحملهولك\n"
        "🎵 اكتب mp3 قبل اللينك لتحميل صوت\n\n"
        "مثال:\nmp3 https://..."
    )

# /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message,
        "📖 طريقة الاستخدام:\n\n"
        "🎥 فيديو: ابعت لينك بس\n"
        "🎵 صوت: اكتب mp3 قبل اللينك\n\n"
        "⏳ استنى 5 ثواني بين كل تحميل"
    )

# التعامل مع الرسائل
@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # منع السبام
    if not can_download(user_id):
        bot.reply_to(message, "⏳ استنى شوية قبل ما تبعت تاني")
        return

    if "http" not in text:
        bot.reply_to(message, "❌ ابعت لينك صحيح")
        return

    msg = bot.reply_to(message, "⏳ جاري التحميل...")

    try:
        # 🔥 تحميل mp3
        if text.startswith("mp3"):
            url = text.replace("mp3", "").strip()

            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s',
                'quiet': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            for file in os.listdir():
                if file.endswith(".mp3"):
                    with open(file, "rb") as audio:
                        bot.send_audio(message.chat.id, audio)
                    os.remove(file)
                    break

        # 🎥 تحميل فيديو
        else:
            url = text

            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': 'video.%(ext)s',
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            for file in os.listdir():
                if file.startswith("video"):
                    with open(file, "rb") as video:
                        bot.send_video(message.chat.id, video)
                    os.remove(file)
                    break

        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(
            f"❌ حصل خطأ:\n{e}",
            message.chat.id,
            msg.message_id
        )

print("🔥 Bot is running...")
bot.infinity_polling()
