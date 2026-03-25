import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 ازيك يزمكس! ابعت لينك وأنا هحملهولك 🔥")

@bot.message_handler(commands=['hello'])
def hello(message):
    bot.reply_to(message, "❤️ عامل ايه يا نجم؟")

@bot.message_handler(func=lambda message: True)
def all_messages(message):
    bot.reply_to(message, "📩 وصلتني الرسالة يا معلم")

print("Bot is running...")

bot.infinity_polling()
