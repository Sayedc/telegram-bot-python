import telebot
import os
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


# 🔥 تحميل الفيديو (نسخة متظبطة)
def download_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        if not filename.endswith(".mp4"):
            filename = filename.split(".")[0] + ".mp4"

        return filename


# 🚀 start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 ازيك يا نجم!\n🔥 ابعتلي أي لينك وأنا احملهولك")


# ❤️ hello
@bot.message_handler(commands=['hello'])
def hello(message):
    bot.reply_to(message, "❤️ عامل ايه يا حبيبي؟")


# 🧠 كل الرسائل
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.lower()

    # 🎬 لو لينك
    if text.startswith("http"):
        msg = bot.reply_to(message, "⏳ ثانية يا معلم بنحمل الفيديو...")

        try:
            file_path = download_video(text)

            # حذف رسالة التحميل
            bot.delete_message(message.chat.id, msg.message_id)

            with open(file_path, 'rb') as video:
                bot.send_video(message.chat.id, video)

            os.remove(file_path)

            bot.send_message(message.chat.id, "🔥 الفيديو وصل يا نجم!")

        except Exception as e:
            bot.delete_message(message.chat.id, msg.message_id)
            print(e)
            bot.reply_to(message, f"❌ حصل مشكلة:\n{e}")

    # 💬 ردود ذكية
    elif "ازيك" in text or "عامل ايه" in text:
        bot.reply_to(message, "❤️ تمام يا حبيبي وانت؟")

    elif "عايز" in text and "فيديو" in text:
        bot.reply_to(message, "📥 ابعت اللينك بس وأنا أظبطهولك")

    elif "شكرا" in text or "thx" in text:
        bot.reply_to(message, "❤️ حبيبي يا معلم")

    elif "hi" in text or "hello" in text or "هلو" in text:
        bot.reply_to(message, "👋 نورت يا نجم")

    else:
        bot.reply_to(message, "📩 وصلت رسالتك يا معلم")


# ▶️ تشغيل
print("Bot is running...")
bot.infinity_polling()
