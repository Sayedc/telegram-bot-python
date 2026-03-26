import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

user_data_store = {}

# 🎬 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 أهلاً بيك يا نجم!\nابعتلي اسم أغنية أو لينك وأنا أظبطهالك 😎")

# 🔍 البحث أو لينك مباشر
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    msg = await update.message.reply_text("🔎 بدورلك... استنى بس 😂")

    # ✅ لو لينك
    if "http" in text:
        user_data_store[chat_id] = {"url": text}

        keyboard = [
            [InlineKeyboardButton("⚡ تحميل فيديو", callback_data="video")],
            [InlineKeyboardButton("🎧 صوت فقط", callback_data="audio")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
        ]

        await msg.edit_text("🎯 اختر اللي انت عايزه:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # 🔎 لو بحث (يوتيوب)
    try:
        ydl_opts = {
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch3:{text}", download=False)
            results = info['entries']

        user_data_store[chat_id] = {"results": results}

        buttons = []
        for i, video in enumerate(results):
            buttons.append([InlineKeyboardButton(video['title'][:40], callback_data=f"select_{i}")])

        buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])

        await msg.edit_text("🎯 اختار الفيديو:", reply_markup=InlineKeyboardMarkup(buttons))

    except:
        await msg.edit_text("❌ مش لاقي حاجة 😢")

# 🎯 اختيار فيديو
async def select_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    if data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء")
        return

    index = int(data.split("_")[1])
    video = user_data_store[chat_id]["results"][index]

    url = video['webpage_url']
    user_data_store[chat_id]["url"] = url

    keyboard = [
        [InlineKeyboardButton("⚡ تحميل فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت فقط", callback_data="audio")],
        [InlineKeyboardButton("🔄 غيره", callback_data="again")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
    ]

    try:
        await query.message.reply_photo(video['thumbnail'], caption=f"🎬 {video['title']}")
    except:
        pass

    await query.edit_message_text("🎥 اختار الجودة:", reply_markup=InlineKeyboardMarkup(keyboard))

# ⚙️ الأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    if data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء")
        return

    if data == "again":
        await query.edit_message_text("🔁 ابعت اسم تاني 😎")
        return

    url = user_data_store.get(chat_id, {}).get("url")

    if not url:
        await query.edit_message_text("❌ حصلت مشكلة")
        return

    await query.edit_message_text("⏳ بحمل اهو... استنى 😂")

    try:
        ydl_opts = {
            'quiet': True,
            'nocheckcertificate': True,
        }

        if data == "audio":
            ydl_opts.update({
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s'
            })
        else:
            ydl_opts.update({
                'format': 'best',
                'outtmpl': 'video.mp4'
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # 📤 إرسال
        if data == "audio":
            file = next((f for f in os.listdir() if f.startswith("audio")), None)
            with open(file, "rb") as f:
                await query.message.reply_audio(f)
            os.remove(file)
        else:
            with open("video.mp4", "rb") as f:
                await query.message.reply_video(f)
            os.remove("video.mp4")

    except Exception as e:
        await query.message.reply_text(f"❌ حصلت مشكلة:\n{e}")

# 🚀 تشغيل
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(select_video, pattern="^select_"))
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
