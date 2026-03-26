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

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🟢 مستخدم جديد:\n👤 {user.first_name}\n🆔 {user_id}"
        )

    await update.message.reply_text("🔥 أهلاً بيك يا نجم 😎")

# تسجيل النشاط
def log_message(user_id):
    user_id = str(user_id)
    if user_id in users_db:
        users_db[user_id]["messages"] += 1
        save_users(users_db)

# استقبال الرسائل
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

# 📊 stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    total = len(users_db)
    msgs = sum(u["messages"] for u in users_db.values())

    await update.message.reply_text(f"👥 المستخدمين: {total}\n💬 الرسائل: {msgs}")

# 📢 broadcast
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    for uid in users_db:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
        except:
            pass

    await update.message.reply_text("✅ تم الإرسال")

# 🚫 ban
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    uid = context.args[0]
    if uid in users_db:
        users_db[uid]["banned"] = True
        save_users(users_db)
        await update.message.reply_text("🚫 تم الحظر")

# ✅ unban
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    uid = context.args[0]
    if uid in users_db:
        users_db[uid]["banned"] = False
        save_users(users_db)
        await update.message.reply_text("✅ تم فك الحظر")

# 🏆 top users
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    top_users = sorted(users_db.items(), key=lambda x: x[1]["messages"], reverse=True)[:5]

    text = "🏆 الأكثر استخدام:\n"
    for u in top_users:
        text += f"{u[1]['name']} - {u[1]['messages']} رسالة\n"

    await update.message.reply_text(text)

# تشغيل
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("top", top))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(select_video, pattern="^select_"))
app.add_handler(CallbackQueryHandler(buttons))

app.run_polling()
