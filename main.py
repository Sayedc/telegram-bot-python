import os
import re
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

CACHE = {}

# استخراج لينك
def extract_url(text):
    match = re.search(r"(https?://[^\s]+)", text)
    return match.group(0) if match else None

# جلب معلومات
def get_info(url):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        return ydl.extract_info(url, download=False)

# البحث
def search(query):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        return info['entries'][0]

# تحميل
def download(url, mode="video"):
    if mode == "audio":
        fmt = "bestaudio"
    else:
        fmt = "best"

    ydl_opts = {
        'format': fmt,
        'outtmpl': '%(id)s.%(ext)s',
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info

# أزرار
def buttons(url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ تحميل سريع", callback_data=f"fast|{url}")],
        [InlineKeyboardButton("⚙ اختيار الجودة", callback_data=f"quality|{url}")]
    ])

def quality_buttons(url):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("360p", callback_data=f"360|{url}")],
        [InlineKeyboardButton("720p", callback_data=f"720|{url}")],
        [InlineKeyboardButton("HD", callback_data=f"best|{url}")]
    ])

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 ابعت لينك أو استخدم /mp3 اسم الأغنية")

# MP3
async def mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)

    if not query:
        await update.message.reply_text("❌ اكتب اسم الأغنية")
        return

    msg = await update.message.reply_text("🔍 بدور...")

    try:
        video = search(query)
        await msg.delete()

        await update.message.reply_photo(
            photo=video["thumbnail"],
            caption=f"{video['title']}\n⏱ {video.get('duration', 0)} sec"
        )

        file, _ = download(video["webpage_url"], "audio")

        await update.message.reply_audio(audio=open(file, "rb"))

        os.remove(file)

    except Exception as e:
        print(e)
        await msg.edit_text("❌ فشل التحميل")

# فيديو
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = context.args[0] if context.args else None

    if not url:
        await update.message.reply_text("❌ ابعت لينك")
        return

    info = get_info(url)

    await update.message.reply_photo(
        photo=info["thumbnail"],
        caption=f"{info['title']}\n⏱ {info.get('duration', 0)} sec",
        reply_markup=buttons(url)
    )

# info
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = context.args[0] if context.args else None

    if not url:
        await update.message.reply_text("❌ ابعت لينك")
        return

    data = get_info(url)

    await update.message.reply_text(
        f"📄 {data['title']}\n👁 {data.get('view_count', 0)} مشاهدة\n⏱ {data.get('duration', 0)} ثانية"
    )

# الرسائل
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    url = extract_url(text)

    if url:
        info = get_info(url)

        await update.message.reply_photo(
            photo=info["thumbnail"],
            caption=f"{info['title']}\n⏱ {info.get('duration', 0)} sec",
            reply_markup=buttons(url)
        )

# الأزرار
async def buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, url = query.data.split("|")

    if url in CACHE:
        await query.message.reply_video(video=open(CACHE[url], "rb"))
        return

    msg = await query.message.reply_text("⏳ جاري التحميل...")

    try:
        if action == "quality":
            await query.message.reply_text("اختار الجودة:", reply_markup=quality_buttons(url))
            return

        if action == "fast":
            file, _ = download(url)

        elif action == "360":
            file, _ = download(url)

        elif action == "720":
            file, _ = download(url)

        else:
            file, _ = download(url)

        CACHE[url] = file

        await query.message.reply_video(video=open(file, "rb"))
        await msg.delete()

    except Exception as e:
        print(e)
        await msg.edit_text("❌ حصل خطأ")

# تشغيل
def main():
    print("🚀 Running...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mp3", mp3))
    app.add_handler(CommandHandler("video", video))
    app.add_handler(CommandHandler("info", info))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(CallbackQueryHandler(buttons_handler))

    app.run_polling()

if __name__ == "__main__":
    main()            os.remove(file_path)

    except Exception as e:
        print("ERROR:", e)
        await msg.edit_text("❌ حصل خطأ")

# تشغيل البوت
def main():
    print("🚀 Bot is running...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

# أهم سطر (التفعيل)
if __name__ == "__main__":
    main()

print("Bot is running...")
app.run_polling()
