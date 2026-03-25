import os
import re
import yt_dlp
import asyncio
from threading import Thread
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= Flask =================
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "🔥 Sayed Bot V21 شغال!"

def run_web():
    app_web.run(host="0.0.0.0", port=8080)

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")

# ================= UTILS =================
def extract_url(text):
    urls = re.findall(r'(https?://\S+)', text)
    return urls[0] if urls else None

def search_youtube(query):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch:{query}", download=False)
        return result['entries'][0]['webpage_url']

def download(url, format_type):
    ydl_opts = {
        'outtmpl': 'file.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'format': format_type,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for f in os.listdir():
        if f.startswith("file"):
            return f

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 اهلا بيك في Sayed Bot V21\n\n"
        "📥 ابعت لينك فيديو او اسم اغنية وانا هجبها لك 😎"
    )

# ================= HANDLE MESSAGE =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    url = extract_url(text)

    # لو مفيش لينك -> سيرش
    if not url:
        msg = await update.message.reply_text("🔍 بدور علي اللي طلبته...")
        try:
            url = search_youtube(text)
        except:
            await msg.edit_text("❌ ملقتش حاجة")
            return

    context.user_data["url"] = url

    keyboard = [
        [InlineKeyboardButton("⚡ تحميل سريع", callback_data="fast")],
        [
            InlineKeyboardButton("360p ⚡", callback_data="360"),
            InlineKeyboardButton("720p 🔥", callback_data="720"),
        ],
        [
            InlineKeyboardButton("HD 💎", callback_data="hd"),
            InlineKeyboardButton("🎧 صوت فقط", callback_data="audio"),
        ],
        [InlineKeyboardButton("❌ الغاء", callback_data="cancel")],
    ]

    await update.message.reply_text(
        "🎬 اختار الجودة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("url")

    if query.data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء")
        return

    await query.edit_message_text("⏳ جاري التحميل...")

    try:
        if query.data == "fast":
            file = download(url, "best")

        elif query.data == "360":
            file = download(url, "bestvideo[height<=360]+bestaudio/best[height<=360]")

        elif query.data == "720":
            file = download(url, "bestvideo[height<=720]+bestaudio/best[height<=720]")

        elif query.data == "hd":
            file = download(url, "bestvideo+bestaudio")

        elif query.data == "audio":
            file = download(url, "bestaudio")

        else:
            await query.edit_message_text("❌ اختيار غلط")
            return

        # ارسال
        if query.data == "audio":
            with open(file, "rb") as f:
                await query.message.reply_audio(f)
        else:
            with open(file, "rb") as f:
                await query.message.reply_video(f)

        os.remove(file)

    except Exception as e:
        await query.message.reply_text("❌ حصل خطأ أثناء التحميل")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(buttons))

    print("🔥 Bot Started...")
    app.run_polling()

# ================= RUN =================
if __name__ == "__main__":
    Thread(target=run_web).start()
    main()
