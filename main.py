import telebot
import os
import yt_dlp

# التوكن من Railway
TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)


# 🎬 تحميل فيديو من أي لينك
def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename


# 🚀 أوامر أساسية
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 ازيك يا نجم!\n\n🔥 ابعتلي أي لينك فيديو وأنا احملهولك فورًا")


@bot.message_handler(commands=['hello'])
def hello(message):
    bot.reply_to(message, "❤️ عامل ايه يا حبيبي؟")


# 🧠 رد ذكي على أي كلام
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.lower()

    # 📌 لو لينك
    if text.startswith("http"):
        try:
            bot.reply_to(message, "⏳ ثانية يا معلم بنحمل الفيديو...")

            file_path = download_video(text)

            with open(file_path, 'rb') as video:
                bot.send_video(message.chat.id, video)

            os.remove(file_path)

            bot.send_message(message.chat.id, "🔥 الفيديو وصل يا نجم!")

        except Exception as e:
            bot.reply_to(message, "❌ حصل مشكلة في اللينك جرب واحد تاني")

    # 💬 ردود ذكية
    elif "ازيك" in text or "عامل ايه" in text:
        bot.reply_to(message, "❤️ تمام يا حبيبي وانت؟")

    elif "عايز" in text and "فيديو" in text:
        bot.reply_to(message, "📥 ابعت اللينك بس وأنا أظبطهولك")

    elif "شكرا" in text or "thx" in text:
        bot.reply_to(message, "❤️ حبيبي يا معلم تحت أمرك")

    elif "hi" in text or "hello" in text or "هلو" in text:
        bot.reply_to(message, "👋 نورت يا نجم")

    else:
        bot.reply_to(message, "📩 وصلت رسالتك يا معلم")


# ▶️ تشغيل البوت
print("Bot is running...")
bot.infinity_polling()
