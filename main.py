import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# تخزين اللينك مؤقت
user_links = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ابعت لينك وأنا أخليك تختار الجودة 😎🔥")

# لما يبعت لينك
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_links[update.message.chat_id] = url

    keyboard = [
        [InlineKeyboardButton("⚡ سريع (720p)", callback_data="fast")],
        [InlineKeyboardButton("🔥 HD (أعلى جودة)", callback_data="hd")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("اختار الجودة:", reply_markup=reply_markup)

# لما يختار الجودة
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data
    chat_id = query.message.chat_id
    url = user_links.get(chat_id)

    msg = await query.message.reply_text("⏳ جاري التحميل...")
