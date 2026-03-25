import os
import yt_dlp
import time
import random
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME = "Sayed_video_bot"

DATA_FILE = "data.json"

# تحميل البيانات
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# تسجيل المستخدم
def register_user(user_id):
    data = load_data()
    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {"invites": 0}
        data["count"] += 1
        save_data(data)

# 🤖 ردود بسيطة
def smart_reply(text):
    text = text.lower()
    if "ازيك" in text:
        return "زي الفل 😎"
    elif "hello" in text:
        return "Hello 🔥"
    elif "نكت" in text:
        return random.choice([
            "مرة واحد غبي وقع من السلم قال انا نازل 😂",
            "مرة واحد دخل امتحان جغرافيا ضاع 😂"
        ])
    else:
        return "😂 ابعت لينك بس"

# Anti-spam
users = {}
def can_use(user_id):
    now = time.time()
    if user_id in users and now - users[user_id] < 5:
        return False
    users[user_id] = now
    return True

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    register_user(user_id)

    data = load_data()
    count = data["count"]

    keyboard = [
        [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 MP3", callback_data="mp3")]
    ]

    await update.message.reply_text(
        f"ازيك 😎\nUsers: {count}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# اختيار النوع
async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["type"] = query.data

    if query.data == "video":
        keyboard = [
            [InlineKeyboardButton("360p", callback_data="360")],
            [InlineKeyboardButton("720p", callback_data="720")],
            [InlineKeyboardButton("1080p", callback_data="1080")]
        ]
        await query.message.reply_text("Quality?", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.message.reply_text("Send link")

# الجودة
async def choose_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["quality"] = query.data
    await query.message.reply_text("Send link")

# الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    register_user(user_id)

    if not can_use(user_id):
        return

    # كلام عادي
    if not text.startswith("http"):
        await update.message.reply_text(smart_reply(text))
        return

    # رسالة واحدة تتعدل
    msg = await update.message.reply_text("⏳")

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
        else:
            ydl_opts = {
                "format": f"mp4[height<={quality}]/best",
                "outtmpl": "video.%(ext)s",
                "quiet": True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([text])

        await msg.edit_text("✅")

        for f in os.listdir():
            if f.endswith(".mp3"):
                await update.message.reply_audio(
                    open(f, "rb"),
                    caption="🎧 Done"
                )
                os.remove(f)

            elif f.startswith("video"):
                await update.message.reply_video(
                    open(f, "rb"),
                    caption="🎬 Done"
                )
                os.remove(f)

        await update.message.reply_text(f"https://t.me/{BOT_USERNAME}")

    except:
        await msg.edit_text("❌")

# تشغيل
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose_type))
app.add_handler(CallbackQueryHandler(choose_quality))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🔥 Running...")
app.run_polling()
