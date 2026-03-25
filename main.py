import os
import re
import yt_dlp
import asyncio
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from threading import Thread
import uvicorn

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ================== API + WEBSITE ==================
app_api = FastAPI()

# ربط الملفات (HTML)
app_api.mount("/static", StaticFiles(directory="."), name="static")

@app_api.get("/")
def home():
    return FileResponse("index.html")

# تحميل الفيديو
def download(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(id)s.%(ext)s',
        'quiet': True,
        'merge_output_format': 'mp4'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# API تحميل
@app_api.get("/download")
def api_download(url: str):
    try:
        file = download(url)
        return FileResponse(file, filename="video.mp4")
    except Exception as e:
        print(e)
        return {"status": "error"}

# ================== BOT ==================

# استخراج اللينك
def extract_url(text):
    match = re.search(r"(https?://[^\s]+)", text)
    return match.group(0) if match else None

# أزرار
def buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 تحميل", callback_data="download")]
    ])

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 ابعت لينك وأنا أحملهولك 😎")

# استقبال الرسائل
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    url = extract_url(text)

    if not url:
        await update.message.reply_text("❌ ابعت لينك صحيح")
        return

    context.user_data['url'] = url

    await update.message.reply_text("اضغط تحميل 👇", reply_markup=buttons())

# الضغط على الزر
async def click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('url')

    msg = await query.message.reply_text("⏳ جاري التحميل...")

    try:
        file = await asyncio.to_thread(download, url)

        await query.message.reply_video(video=open(file, "rb"))

        os.remove(file)
        await msg.delete()

    except Exception as e:
        print(e)
        await msg.edit_text("❌ حصل خطأ")

# تشغيل البوت
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(CallbackQueryHandler(click))

    print("🤖 Bot Running...")
    app.run_polling()

# ================== تشغيل الكل ==================
if __name__ == "__main__":
    Thread(target=run_bot).start()
    uvicorn.run(app_api, host="0.0.0.0", port=8000)
    
