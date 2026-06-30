# handlers/errors.py
from telegram import Update
from telegram.ext import ContextTypes


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج الأخطاء العام
    """
    try:
        raise context.error
    except Exception as e:
        error_text = f"⚠️ حدث خطأ: {str(e)[:100]}"

        if update and update.effective_message:
            await update.effective_message.reply_text(error_text)

        print(f"❌ ERROR: {e}")
