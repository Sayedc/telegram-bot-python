import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# تخزين بيانات المستخدم
user_data_store = {}

# 🎬 START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 أهلاً بيك يا نجم!\nابعتلي اسم أغنية أو لينك وأنا أظبطهالك 😎")

# 🔍 البحث
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    msg = await update.message.reply_text("🔎 بدورلك... استنى بس متجريش 😂")

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(f"ytsearch3:{text}", download=False)
            results = info['entries']

        user_data_store[chat_id] = {"results": results}

        buttons = []
        for i, video in enumerate(results):
            buttons.append([InlineKeyboardButton(video['title'][:40], callback_data=f"select_{i}")])

        buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])

        await msg.edit_text("🎯 اختار الفيديو اللي عاجبك:", reply_markup=InlineKeyboardMarkup(buttons))

    except:
        await msg.edit_text("❌ مش لاقي حاجة خالص 😢")

# 🎯 اختيار فيديو
async def select_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    if data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء يا معلم")
        return

    index = int(data.split("_")[1])
    video = user_data_store[chat_id]["results"][index]

    user_data_store[chat_id]["url"] = video['webpage_url']

    keyboard = [
        [InlineKeyboardButton("⚡ 360p", callback_data="360")],
        [InlineKeyboardButton("🔥 720p", callback_data="720")],
        [InlineKeyboardButton("💎 HD", callback_data="best")],
        [InlineKeyboardButton("🎧 صوت فقط", callback_data="audio")],
        [InlineKeyboardButton("🔄 نتيجة تانية", callback_data="again")],
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
        await query.edit_message_text("🔁 ابعت اسم تاني وأنا أجيبلك 😎")
        return

    url = user_data_store.get(chat_id, {}).get("url")

    if not url:
        await query.edit_message_text("❌ حصلت مشكلة")
        return

    await query.edit_message_text("⏳ بحمل اهو... متقفلش البوت 😂")

    try:
        if data == "audio":
            ydl_opts = {'format': 'bestaudio', 'outtmpl': 'audio.%(ext)s'}
        elif data == "360":
            ydl_opts = {'format': 'best[height<=360]', 'outtmpl': 'video.mp4'}
        elif data == "720":
            ydl_opts = {'format': 'best[height<=720]', 'outtmpl': 'video.mp4'}
        else:
            ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4'}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if data == "audio":
            file = next((f for f in os.listdir() if f.startswith("audio")), None)
            with open(file, "rb") as f:
                await query.message.reply_audio(f)
        else:
            with open("video.mp4", "rb") as f:
                await query.message.reply_video(f)

    except Exception as e:
        await query.message.reply_text(f"❌ حصلت مشكلة: {e}")

# 🚀 تشغيل
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(select_video, pattern="^select_"))
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
