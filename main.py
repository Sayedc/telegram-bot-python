import os
import re
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# ---------- Smart Replies ----------
def smart_reply(text):
    text = text.lower()

    if "hello" in text or "hi" in text:
        return "👋 اهلا"

    if "ازيك" in text:
        return "تمام 😎"

    if "عامل ايه" in text:
        return "فل 🔥"

    if "مين انت" in text:
        return "Sayed Bot 🤖"

    return "ابعت لينك 🎬"

# ---------- Download ----------
def download(url, audio=False):
    filename = "file.%(ext)s"

    ydl_opts = {
        'outtmpl': filename,
        'quiet': True,
        'noplaylist': True,
    }

    if audio:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best'
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # يرجع اسم الملف الحقيقي
    for f in os.listdir():
        if f.startswith("file"):
            return f

# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Sayed Bot\n"
        "—\n"
        "ابعت لينك 🎬"
    )

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋")

# ---------- Handler ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # كلام عادي
    if not re.search(r"http", text):
        await update.message.reply_text(smart_reply(text))
        return

    msg = await update.message.reply_text("⏳")

    try:
        url = text.split()[-1]

        is_audio = any(word in text.lower() for word in ["mp3", "اغنية", "audio"])

        file = download(url, is_audio)

        await msg.edit_text("✓")

        if is_audio:
            await update.message.reply_audio(
                audio=open(file, 'rb'),
                caption="🎧"
            )
        else:
            await update.message.reply_video(
                video=open(file, 'rb'),
                caption="🎬"
            )

        os.remove(file)

    except:
        await msg.edit_text("✗")

# ---------- Run ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("hello", hello))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Running...")

app.run_polling()    # كلام عادي
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
