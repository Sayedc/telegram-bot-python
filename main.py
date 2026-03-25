import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ BOT_TOKEN مش موجود")
    exit()

bot = telebot.TeleBot(TOKEN)

print("🚀 Bot started...")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 ازيك يا نجم! ابعت لينك وانا احملهولك 🔥")

@bot.message_handler(commands=['hello'])
def hello(message):
    bot.reply_to(message, "❤️ حبيبي عامل ايه؟")

@bot.message_handler(func=lambda message: True)
def all_messages(message):
    bot.reply_to(message, "📩 وصلت رسالتك يا معلم")

# 👇 أهم سطر (مع حماية من الكراش)
while True:
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"❌ Error: {e}")
