import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

user_data = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ابعت لينك وأنا أظبطهولك 🔥")

# استقبال اللينك
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_data[update.message.chat_id] = {"url": url}

    keyboard = [
        [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت فقط", callback_data="audio")]
    ]

    await update.message.reply_text("اختار النوع:", reply_markup=InlineKeyboardMarkup(keyboard))

# اختيار النوع
async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user_data[chat_id]["type"] = query.data

    if query.data == "video":
        keyboard = [
            [InlineKeyboardButton("⚡ 360p", callback_data="360")],
            [InlineKeyboardButton("🔥 720p", callback_data="720")],
            [InlineKeyboardButton("💎 HD", callback_data="hd")]
        ]
        await query.message.reply_text("اختار الجودة:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await download(update, context)

# اختيار الجودة
async def choose_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user_data[chat_id]["quality"] = query.data

    await download(update, context)

# التحميل
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = user_data.get(chat_id)

    url = data["url"]
    file_type = data.get("type")
    quality = data.get("quality")

    msg = await query.message.reply_text("⏳ جاري التحميل...")

    try:
        if file_type == "audio":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s',
                'quiet': True,
                'no_warnings': True
            }
        else:
            if quality == "360":
                fmt = 'best[height<=360]'
            elif quality == "720":
                fmt = 'best[height<=720]'
            else:
                fmt = 'bestvideo+bestaudio/best'

            ydl_opts = {
                'format': fmt,
                'outtmpl': 'video.%(ext)s',
                'merge_output_format': 'mp4',
                'quiet': True,
                'no_warnings': True
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await msg.delete()

        with open(filename, 'rb') as f:
            if file_type == "audio":
                await query.message.reply_audio(audio=f)
            else:
                await query.message.reply_document(document=f)

        os.remove(filename)

        await query.message.reply_text("🔥 تم التحميل!")

    except Exception as e:
        await msg.delete()
        print(e)
        await query.message.reply_text("❌ حصل خطأ")

# تشغيل البوت
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(choose_type, pattern="^(video|audio)$"))
app.add_handler(CallbackQueryHandler(choose_quality, pattern="^(360|720|hd)$"))

print("Bot is running...")
app.run_polling()
