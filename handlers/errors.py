# handlers/errors.py
import logging

from telegram import Update
from telegram.error import BadRequest, Conflict, NetworkError, TimedOut
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج الأخطاء العام.

    * يكتب الـ traceback كامل في logs/errors.log (سجل الأخطاء بتاع الأدمن).
    * مبيبعتش نص الاستثناء للمستخدم (ممكن يكشف مسارات أو بيانات داخلية).
    * بيتجاهل الأخطاء المزعجة اللي مش مشكلة فعلية.
    """
    error = context.error

    if isinstance(error, Conflict):
        logger.error(
            "Conflict: another instance of the bot is running with the same token."
        )
        return

    if isinstance(error, BadRequest):
        if "message is not modified" in str(error).lower():
            return  # user pressed the same button twice
    elif isinstance(error, (TimedOut, NetworkError)):
        logger.warning("Network problem talking to Telegram: %s", error)
        return

    logger.error("Unhandled exception while handling an update", exc_info=error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ حصل خطأ غير متوقع. حاول تاني بعد شوية."
            )
        except Exception:  # noqa: BLE001
            pass
