import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8137693278:AAEwPTeHj8JEwglERKzKvDdAAabAX1Gs08I"

# إنشاء فولدر downloads
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_data_store = {}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 ابعت لينك أو اسم فيديو وأنا أظبطهالك 😎")

# استقبال الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    msg = await update.message.reply_text("🔎 بدورلك...")

    if "http" in text:
        user_data_store[chat_id] = {"url": text}

        keyboard = [
            [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
            [InlineKeyboardButton("🎧 صوت فقط", callback_data="audio")],
            [InlineKeyboardButton("📸 صور", callback_data="photos")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
        ]

        await msg.edit_text("🎯 اختار:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # بحث
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(f"ytsearch3:{text}", download=False)
            results = info['entries']

        user_data_store[chat_id] = {"results": results}

        buttons = []
        for i, video in enumerate(results):
            buttons.append([InlineKeyboardButton(video['title'][:40], callback_data=f"select_{i}")])

        buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])

        await msg.edit_text("🎯 اختار الفيديو:", reply_markup=InlineKeyboardMarkup(buttons))

    except:
        await msg.edit_text("❌ مش لاقي حاجة")

# اختيار فيديو
async def select_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    index = int(query.data.split("_")[1])

    video = user_data_store[chat_id]["results"][index]
    url = video['webpage_url']

    user_data_store[chat_id]["url"] = url

    keyboard = [
        [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت فقط", callback_data="audio")],
        [InlineKeyboardButton("📸 صور", callback_data="photos")],
        [InlineKeyboardButton("🔄 غيره", callback_data="again")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
    ]

    await query.edit_message_text("🎥 اختار:", reply_markup=InlineKeyboardMarkup(keyboard))

# الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    if data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء")
        return

    if data == "again":
        await query.edit_message_text("🔁 ابعت حاجة تانية")
        return

    url = user_data_store.get(chat_id, {}).get("url")

    if not url:
        await query.edit_message_text("❌ حصلت مشكلة")
        return

    await query.edit_message_text("⏳ بحمل...")

    try:
        ydl_opts = {
            'quiet': True,
            'noplaylist': False,
            'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # 🎧 صوت
        if data == "audio":
            audio_file = None
            for f in os.listdir(DOWNLOAD_DIR):
                if f.endswith(('.mp3', '.m4a', '.webm')):
                    audio_file = f
                    break

            if audio_file:
                path = os.path.join(DOWNLOAD_DIR, audio_file)
                await query.message.reply_audio(open(path, "rb"))
                os.remove(path)

        # 📸 صور TikTok
        elif data == "photos":
            if info.get("_type") == "playlist" or isinstance(info.get("entries"), list):
                for entry in info["entries"]:
                    file_path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(entry)
                    if os.path.exists(file_path):
                        await query.message.reply_photo(open(file_path, "rb"))
                        os.remove(file_path)
            else:
                await query.message.reply_text("❌ اللينك مش صور")

        # 🎬 فيديو
        else:
            video_file = None
            for f in os.listdir(DOWNLOAD_DIR):
                if f.endswith(('.mp4', '.mkv', '.webm')):
                    video_file = f
                    break

            if video_file:
                path = os.path.join(DOWNLOAD_DIR, video_file)
                await query.message.reply_video(open(path, "rb"))
                os.remove(path)

    except Exception as e:
        await query.message.reply_text(f"❌ {e}")

# تشغيل
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(select_video, pattern="^select_"))
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
