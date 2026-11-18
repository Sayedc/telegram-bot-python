# handlers/user.py
from telegram import Update
from telegram.ext import ContextTypes

from database.user_repository import (
    get_user,
    get_users,
    update_last_seen,
    increase_downloads,
)


async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض ملف المستخدم"""
    user_id = update.effective_user.id
    user_data = get_user(user_id)

    if not user_data:
        await update.message.reply_text("❌ لا توجد بيانات لك")
        return

    # تحديث آخر ظهور
    update_last_seen(user_id)

    text = f"""
👤 *ملف المستخدم*

🆔 المعرف: `{user_id}`
📛 الاسم: {user_data.get('name', 'غير معروف')}
📥 عدد التحميلات: {user_data.get('downloads', 0)}
📅 تاريخ الانضمام: {user_data.get('joined', 'غير معروف')}
"""

    await update.message.reply_text(text, parse_mode="Markdown")


async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات المستخدم من خلال الأزرار"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = get_user(user_id)

    if not user_data:
        await query.edit_message_text("❌ لا توجد بيانات لك")
        return

    text = f"""
📊 *إحصائياتك الشخصية*

📥 التحميلات: {user_data.get('downloads', 0)}
🚫 الحالة: {'محظور' if user_data.get('blocked') else 'نشط'}
📅 تاريخ الانضمام: {user_data.get('joined', 'غير معروف')[:10]}
"""

    await query.edit_message_text(text, parse_mode="Markdown")
