import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8137693278:AAEwPTeHj8JEwglERKzKvDdAAabAX1Gs08I"

user_data_store = {}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 ابعت لينك أو اسم فيديو وأنا أظبطهالك 😎")

# استقبال الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    msg = await update.message.reply_text("🔎 بدورلك...")

    # لو لينك مباشر
    if "http" in text:
        user_data_store[chat_id] = {"url": text}

        keyboard = [
            [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
            [InlineKeyboardButton("🎧 صوت فقط", callback_data="audio")],
            [InlineKeyboardButton("📸 صورة", callback_data="photo")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
        ]

        await msg.edit_text("🎯 اختار اللي انت عايزه:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # لو بحث
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
        [InlineKeyboardButton("📸 صورة", callback_data="photo")],
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
            'noplaylist': True,
        }

        # 🎧 صوت
        if data == "audio":
            ydl_opts.update({
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s'
            })

        # 📸 صورة (thumbnail)
        elif data == "photo":
            ydl_opts.update({
                'skip_download': True
            })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                thumb = info.get("thumbnail")

            if thumb:
                await query.message.reply_photo(thumb)
            else:
                await query.message.reply_text("❌ مفيش صورة متاحة")

            return

        # 🎬 فيديو
        else:
            ydl_opts.update({
                'format': 'best',
                'outtmpl': 'video.mp4'
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # إرسال
        if data == "audio":
            file = next((f for f in os.listdir() if f.startswith("audio")), None)
            await query.message.reply_audio(open(file, "rb"))
            os.remove(file)
        else:
            await query.message.reply_video(open("video.mp4", "rb"))
            os.remove("video.mp4")

    except Exception as e:
        await query.message.reply_text(f"❌ {e}")

# تشغيل
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(select_video, pattern="^select_"))
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
