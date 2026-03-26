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

# تحميل البيانات
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# حفظ البيانات
def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

users_db = load_users()

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)

    if user_id not in users_db:
        users_db[user_id] = {
            "name": user.first_name,
            "join_date": str(datetime.now()),
            "messages": 0,
            "banned": False
        }
        save_users(users_db)

        # إشعار للأدمن
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🟢 مستخدم جديد:\n👤 {user.first_name}\n🆔 {user_id}"
        )

    total_users = len(users_db)

    # 👇 الفرق هنا
    if update.message.chat_id == ADMIN_ID:
        text = (
            f"🔥 أهلاً بيك يا أدمن 😎\n\n"
            f"👥 عدد المستخدمين: {total_users}\n\n"
            f"📥 البوت شغال تمام"
        )
    else:
        text = (
            f"🔥 أهلاً بيك 😎\n\n"
            f"📥 ابعت لينك أو اسم فيديو وأنا أحملهولك"
        )

    await update.message.reply_text(text)

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

    # لو لينك
    if "http" in text:
        user_data_store[chat_id] = {"url": text}

        keyboard = [
            [InlineKeyboardButton("⚡ فيديو", callback_data="video")],
            [InlineKeyboardButton("🎧 صوت", callback_data="audio")],
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

    if not url:
        await query.edit_message_text("❌ حصلت مشكلة")
        return

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
            with open(file, "rb") as f:
                await query.message.reply_audio(f)
            os.remove(file)
        else:
            with open("video.mp4", "rb") as f:
                await query.message.reply_video(f)
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
