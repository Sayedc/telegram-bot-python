import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

TOKEN = "8137693278:AAEwPTeHj8JEwglERKzKvDdAAabAX1Gs08I"

# حفظ اللينك مؤقت
user_links = {}

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 ابعت لينك فيديو وأنا أظبطهالك 😎")

# استقبال اللينك
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import re

text = update.message.text

# استخراج أول لينك من الرسالة
urls = re.findall(r'(https?://\S+)', text)

if not urls:
    await update.message.reply_text("❌ ابعت لينك صحيح")
    return

url = urls[0]
    user_id = update.message.from_user.id

    user_links[user_id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎥 فيديو", callback_data="video"),
            InlineKeyboardButton("🎵 صوت", callback_data="audio"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("اختار نوع التحميل:", reply_markup=reply_markup)

# التعامل مع الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_links:
        await query.edit_message_text("❌ مفيش لينك")
        return

    url = user_links[user_id]

    await query.edit_message_text("⏳ جاري التحميل...")

    try:
        if query.data == "video":
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'video.mp4'
            }

        elif query.data == "audio":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.mp3',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if query.data == "video":
            await context.bot.send_video(chat_id=query.message.chat_id, video=open("video.mp4", "rb"))

        else:
            await context.bot.send_audio(chat_id=query.message.chat_id, audio=open("audio.mp3", "rb"))

    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ حصل خطأ:\n{e}")

    finally:
        if os.path.exists("video.mp4"):
            os.remove("video.mp4")
        if os.path.exists("audio.mp3"):
            os.remove("audio.mp3")

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")
app.run_polling()
