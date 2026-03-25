import os
import yt_dlp
import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME = "Sayed_video_bot"

# 😎 رسائل
WELCOME = "ازيك يزمكس 😎🔥\nاختار اللي انت عايزه وبعدين ابعت اللينك 👇"
DONE = f"يلا الفيديو جالك 😂🔥\n📩 ابعت البوت لصحابك:\nhttps://t.me/{BOT_USERNAME}"
ERROR = "❌ اللينك غلط يا نجم.. جرب واحد تاني"
WAIT = "⏳ ثانية يا معلم..."

# 🤖 ذكاء مجاني
def smart_reply(text):
    text = text.lower()

    if "ازيك" in text:
        return "زي الفل يا نجم 😎"
    elif "hello" in text:
        return "Hello ya bro 🔥"
    elif "نكت" in text:
        return random.choice([
            "مرة واحد غبي وقع من السلم قال انا نازل 😂",
            "مرة واحد دخل امتحان جغرافيا ضاع 😂"
        ])
    else:
        return random.choice([
            "😂 ابعت لينك يا عم",
            "😎 قول حاجة مفهومة",
        ])

# 🛑 Anti-spam
users = {}
def can_use(user_id):
    now = time.time()
    if user_id in users and now - users[user_id] < 5:
        return False
    users[user_id] = now
    return True

# 🎮 لعبة
games = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 MP3", callback_data="mp3")],
        [InlineKeyboardButton("🎮 لعبة", callback_data="game")]
    ]
    await update.message.reply_text(WELCOME, reply_markup=InlineKeyboardMarkup(keyboard))

# اختيار النوع
async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "game":
        number = random.randint(1, 10)
        games[query.from_user.id] = number
        await query.message.reply_text("🎮 خمنت رقم من 1 لـ 10.. حاول 😏")
        return

    context.user_data["type"] = query.data

    if query.data == "video":
        keyboard = [
            [InlineKeyboardButton("360p", callback_data="360")],
            [InlineKeyboardButton("720p", callback_data="720")],
            [InlineKeyboardButton("1080p", callback_data="1080")]
        ]
        await query.message.reply_text("اختار الجودة 👇", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.message.reply_text("ابعت اللينك 👇")

# الجودة
async def choose_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["quality"] = query.data
    await query.message.reply_text("ابعت اللينك 👇")

# الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # لعبة
    if user_id in games:
        if text.isdigit():
            if int(text) == games[user_id]:
                await update.message.reply_text("🎉 صح!")
            else:
                await update.message.reply_text("❌ غلط")
            del games[user_id]
            return

    # ذكاء
    if not text.startswith("http"):
        await update.message.reply_text(smart_reply(text))
        return

    # سبام
    if not can_use(user_id):
        await update.message.reply_text("⏳ استنى شوية")
        return

    await update.message.reply_text(WAIT)

    file_type = context.user_data.get("type", "video")
    quality = context.user_data.get("quality", "720")

    try:
        if file_type == "mp3":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "audio.%(ext)s",
                "quiet": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            for f in os.listdir():
                if f.endswith(".mp3"):
                    await update.message.reply_audio(open(f, "rb"))
                    os.remove(f)

        else:
            ydl_opts = {
                "format": f"mp4[height<={quality}]/best",
                "outtmpl": "video.%(ext)s",
                "quiet": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])

            for f in os.listdir():
                if f.startswith("video"):
                    await update.message.reply_video(open(f, "rb"))
                    os.remove(f)

        await update.message.reply_text(DONE)

    except:
        await update.message.reply_text(ERROR)

# تشغيل
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose_type))
app.add_handler(CallbackQueryHandler(choose_quality))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🔥 Bot is running...")
app.run_polling()
