import telebot
import os
import yt_dlp
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


# 🔧 إصلاح لينك TikTok
def fix_tiktok_url(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=5)
        return r.url
    except:
        return url


# 🎬 تحميل فيديو
def download_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0'}
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        if not filename.endswith(".mp4"):
            filename = filename.split(".")[0] + ".mp4"

        return filename


# 🎧 تحميل MP3
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)
        return "audio.mp3"


# 🎯 أزرار
def get_buttons(url):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎬 فيديو", callback_data=f"video|{url}"),
        InlineKeyboardButton("🎧 MP3", callback_data=f"audio|{url}")
    )
    return markup


# 🚀 start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 ازيك يا نجم!\n🔥 ابعت لينك وأنا أظبطهولك")


# ❤️ hello
@bot.message_handler(commands=['hello'])
def hello(message):
    bot.reply_to(message, "❤️ عامل ايه يا حبيبي؟")


# 📩 استقبال لينكات
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text

    if text.startswith("http"):
        fixed_url = fix_tiktok_url(text)

        # ❌ منع اللينكات الغلط
        if "explore" in fixed_url or "?_r" in fixed_url:
            bot.reply_to(message, "❌ اللينك ده مش فيديو\nابعت من زرار Share")
            return

        bot.reply_to(message, "👇 اختار اللي انت عايزه:", reply_markup=get_buttons(fixed_url))
        return

    # 💬 ردود ذكية
    if "ازيك" in text:
        bot.reply_to(message, "❤️ تمام يا حبيبي وانت؟")

    elif "عامل ايه" in text:
        bot.reply_to(message, "🔥 فل زيك يا نجم")

    elif "شكرا" in text:
        bot.reply_to(message, "❤️ حبيبي يا معلم")

    elif "هلو" in text or "hello" in text or "hi" in text:
        bot.reply_to(message, "👋 نورت يا كبير")

    elif "عايز" in text and "فيديو" in text:
        bot.reply_to(message, "📥 ابعت اللينك وأنا أحملهولك")

    else:
        bot.reply_to(message, "📩 وصلت يا معلم")


# 🎯 التعامل مع الأزرار
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    data = call.data.split("|")
    action = data[0]
    url = data[1]

    msg = bot.send_message(call.message.chat.id, "⏳ جاري التحميل...")

    try:
        if action == "video":
            file_path = download_video(url)

            with open(file_path, 'rb') as f:
                bot.send_video(call.message.chat.id, f)

            os.remove(file_path)
            bot.send_message(call.message.chat.id, "🔥 الفيديو وصل")

        elif action == "audio":
            file_path = download_audio(url)

            with open(file_path, 'rb') as f:
                bot.send_audio(call.message.chat.id, f)

            os.remove(file_path)
            bot.send_message(call.message.chat.id, "🎧 الصوت وصل")

    except Exception as e:
        print(e)
        bot.send_message(call.message.chat.id, f"❌ حصل مشكلة:\n{e}")

    bot.delete_message(call.message.chat.id, msg.message_id)


print("Bot is running...")
bot.infinity_polling()
