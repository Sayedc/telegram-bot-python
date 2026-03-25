import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🎬 Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 أهلاً بيك يا نجم!\n\n"
        "ابعت لينك فيديو أو اسم أغنية وأنا أظبطهالك 😎"
    )

# 🔍 تحميل البيانات
def get_info(query):
    ydl_opts = {
        'quiet': True,
        'format': 'best'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
    return info

# 📩 استقبال الرسالة
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    await update.message.reply_text("🔎 بدورلك على الطلب...")

    try:
        info = get_info(f"ytsearch1:{text}" if "http" not in text else text)

        if "entries" in info:
            info = info["entries"][0]

        context.user_data["url"] = info["webpage_url"]

        keyboard = [
            [InlineKeyboardButton("⚡ 360p", callback_data="360")],
            [InlineKeyboardButton("🔥 720p", callback_data="720")],
            [InlineKeyboardButton("💎 HD", callback_data="best")],
            [InlineKeyboardButton("🎧 صوت فقط", callback_data="audio")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🎬 لقيتلك:\n{info['title']}\n\nاختار الجودة 👇",
            reply_markup=reply_markup
        )

    except:
        await update.message.reply_text("❌ حصلت مشكلة يا نجم")

# ⬇️ تحميل
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data
    url = context.user_data.get("url")

    await query.edit_message_text("⏳ جاري التحميل... استنى شوية")

    try:
        if choice == "audio":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'audio.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3'
                }]
            }
        else:
            format_map = {
                "360": "bestvideo[height<=360]+bestaudio/best",
                "720": "bestvideo[height<=720]+bestaudio/best",
                "best": "bestvideo+bestaudio/best"
            }

            ydl_opts = {
                'format': format_map[choice],
                'outtmpl': 'video.%(ext)s',
                'merge_output_format': 'mp4'
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # إرسال الملف
        for file in os.listdir():
            if file.endswith(".mp4"):
                await query.message.reply_video(open(file, "rb"))
                os.remove(file)
            elif file.endswith(".mp3"):
                await query.message.reply_audio(open(file, "rb"))
                os.remove(file)

        await query.message.reply_text("✅ تم التحميل يا باشا 🔥")

    except Exception as e:
        await query.message.reply_text("❌ حصل خطأ أثناء التحميل")

# 🚀 تشغيل البوت
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(download))

app.run_polling()
