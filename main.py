import os
import re
import telebot
import yt_dlp
from telebot.types import Message

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ردود عشوائية
smart_replies = [
    "قول يا زعيم 👀",
    "تحت أمرك يا نجم 🔥",
    "عايز ايه وأنا أنفذ 😎",
    "معاك يا كبير 💪",
]

# تحقق من اللينك
def is_url(text):
    return re.match(r'https?://', text)

# تحميل الفيديو
def download_video(url):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'best',
        'quiet': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

# /start
@bot.message_handler(commands=['start'])
def start(message: Message):
    bot.reply_to(message, "ازيك يزمكس 😎🔥\nابعتلي لينك وأنا أحملهولك علطول 💪")

# /hello
@bot.message_handler(commands=['hello'])
def hello(message: Message):
    bot.reply_to(message, "هلا والله 😍 عامل ايه؟")

# أي رسالة
@bot.message_handler(func=lambda m: True)
def handle_message(message: Message):
    text = message.text

    # لو مش لينك → رد ذكي
    if not is_url(text):
        bot.reply_to(message, smart_replies[0])
        return

    # رسالة تحميل مؤقتة
    loading_msg = bot.reply_to(message, "⏳ ثانية يا معلم بحمل الفيديو...")

    try:
        file_path = download_video(text)

        # حذف رسالة التحميل
        bot.delete_message(message.chat.id, loading_msg.message_id)

        # ارسال الفيديو
        with open(file_path, 'rb') as video:
            bot.send_video(message.chat.id, video)

        # رسالة نهائية
        bot.send_message(
            message.chat.id,
            "يلا الفيديو جالك 😂🔥\nمش عايزين نشوف وشك هنا تاني 😎"
        )

        # حذف الملف
        os.remove(file_path)

    except Exception as e:
        bot.delete_message(message.chat.id, loading_msg.message_id)
        bot.reply_to(message, "❌ اللينك غلط يا نجم أو مش مدعوم جرب غيره")

# تشغيل البوت
print("Bot is running...")
bot.infinity_polling()
