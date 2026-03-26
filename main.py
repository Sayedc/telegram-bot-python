import os
import yt_dlp
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5671168695
DATA_FILE = "users.json"

user_data_store = {}

def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

users_db = load_users()

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)

    referrer = context.args[0] if context.args else None

    if user_id not in users_db:
        users_db[user_id] = {
            "name": user.first_name,
            "join_date": str(datetime.now()),
            "messages": 0,
            "banned": False,
            "invited_by": referrer,
            "invites": 0
        }

        if referrer and referrer in users_db and referrer != user_id:
            users_db[referrer]["invites"] += 1

        save_users(users_db)

    total_users = len(users_db)
    my_invites = users_db[user_id]["invites"]

    bot_username = (await context.bot.get_me()).username
    my_link = f"https://t.me/{bot_username}?start={user_id}"

    await update.message.reply_text(
        f"🔥 أهلاً بيك 😎\n\n"
        f"👥 المستخدمين: {total_users}\n"
        f"🎁 دعواتك: {my_invites}\n\n"
        f"لينكك:\n{my_link}"
    )

# تسجيل النشاط
def log_message(user_id):
    user_id = str(user_id)
    if user_id in users_db:
        users_db[user_id]["messages"] += 1
        save_users(users_db)

# الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat_id)

    if user_id in users_db and users_db[user_id].get("banned"):
        return

    log_message(user_id)

    text = update.message.text
    chat_id = update.message.chat_id

    msg = await update.message.reply_text("🔎 بدورلك...")

    if "http" in text:
        user_data_store[chat_id] = {"url": text}

        keyboard = [
            [InlineKeyboardButton("⚡ فيديو", callback_data="video")],
            [InlineKeyboardButton("🎧 صوت", callback_data="audio")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
        ]

        await msg.edit_text("🎯 اختار:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(f"ytsearch3:{text}", download=False)
            results = info['entries']

        user_data_store[chat_id] = {"results": results}

        buttons = [[InlineKeyboardButton(v['title'][:40], callback_data=f"select_{i}")]
                   for i, v in enumerate(results)]
        buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])

        await msg.edit_text("🎯 اختار:", reply_markup=InlineKeyboardMarkup(buttons))

    except:
        await msg.edit_text("❌ مش لاقي حاجة")

# اختيار فيديو
async def select_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    index = int(query.data.split("_")[1])

    video = user_data_store[chat_id]["results"][index]
    user_data_store[chat_id]["url"] = video['webpage_url']

    keyboard = [
        [InlineKeyboardButton("⚡ فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت", callback_data="audio")],
        [InlineKeyboardButton("🔄 غيره", callback_data="again")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
    ]

    await query.edit_message_text("🎥 اختار:", reply_markup=InlineKeyboardMarkup(keyboard))

# تحميل
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

    await query.edit_message_text("⏳ بحمل...")

    try:
        ydl_opts = {'quiet': True}

        if data == "audio":
            ydl_opts.update({'format': 'bestaudio', 'outtmpl': 'audio.%(ext)s'})
        else:
            ydl_opts.update({'format': 'best', 'outtmpl': 'video.mp4'})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

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
