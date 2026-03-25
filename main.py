import telebot
import os
import yt_dlp
import requests

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


# 🔥 يصلح لينك TikTok (vt → الفيديو الحقيقي)
def fix_tiktok_url(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=5)
        return r.url
    except:
        return url


# 🎬 تحميل الفيديو
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
    bot.reply_to(message, "👋 ازيك يا نجم!\n🔥 ابعتلي أي لينك فيديو وأنا احملهولك فورًا")


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
            fixed_url = fix_tiktok_url(text)

            # لو اتحول لـ explore → نرفض
            if "explore" in fixed_url:
                bot.delete_message(message.chat.id, msg.message_id)
                bot.reply_to(message, "❌ اللينك ده مش فيديو يا نجم\n📌 ابعت لينك مباشر من TikTok")
                return

            file_path = download_video(fixed_url)

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
        bot.reply_to(message, "📥 ابعت اللينك بس
