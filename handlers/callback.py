from telegram import Update
from telegram.ext import ContextTypes

from keyboards.main_keyboard import main_keyboard, admin_keyboard, admin_panel
from core import is_admin


# =========================
# MAIN CALLBACK HANDLER
# =========================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    # =========================
    # QUALITY SYSTEM
    # =========================
    if data.startswith("q_"):
        value = data.replace("q_", "")

        if value == "audio":
            context.user_data["audio"] = True
            context.user_data["quality"] = None
            await query.edit_message_text("🎵 تم تفعيل وضع الصوت")
        else:
            context.user_data["audio"] = False
            context.user_data["quality"] = value
            await query.edit_message_text(f"⚡ تم اختيار الجودة: {value}p")

        return

    # =========================
    # BACK BUTTON
    # =========================
    if data == "back":
        await query.edit_message_text(
            "🏠 الرئيسية",
            reply_markup=main_keyboard()
        )
        return

    # =========================
    # ADMIN PANEL OPEN
    # =========================
    if data == "admin_panel":
        if not is_admin(user_id):
            await query.edit_message_text("🚫 مش مسموح")
            return

        await query.edit_message_text(
            "👑 لوحة الأدمن",
            reply_markup=admin_panel()
        )
        return

    # =========================
    # ADMIN ACTIONS
    # =========================
    if data == "admin_stats":
        await query.edit_message_text("📊 جاري عرض الإحصائيات...")
        return

    if data == "admin_top":
        await query.edit_message_text("🏆 ترتيب المستخدمين...")
        return

    if data == "admin_users":
        await query.edit_message_text("👥 قائمة المستخدمين...")
        return

    if data == "admin_broadcast":
        await query.edit_message_text("📢 أرسل الرسالة للإذاعة...")
        return

    if data == "admin_clear":
        await query.edit_message_text("🧹 تم تنظيف الكاش")
        return

    if data == "admin_backup":
        await query.edit_message_text("📤 جاري إنشاء نسخة احتياطية...")
        return

    if data == "admin_block":
        await query.edit_message_text("🚫 اكتب ID الحظر")
        return

    if data == "admin_unblock":
        await query.edit_message_text("🔓 اكتب ID فك الحظر")
        return

    if data == "admin_metrics":
        await query.edit_message_text("📊 عرض الأداء...")
        return

    # =========================
    # USER BUTTONS
    # =========================
    if data == "help_video":
        await query.edit_message_text("🎬 ابعت اللينك لتحميل الفيديو")
        return

    if data == "help_audio":
        await query.edit_message_text("🎵 ابعت اللينك لاستخراج الصوت")
        return

    if data == "share_bot":
        await query.edit_message_text("🎁 شارك البوت مع صحابك")
        return

    if data == "my_stats":
        await query.edit_message_text("📊 إحصائياتك هنا")
        return

    if data == "help":
        await query.edit_message_text("❓ المساعدة: ابعت أي رابط وسيتم تحميله")
        return

    # =========================
    # FALLBACK (NO MORE INVALID ACTION)
    # =========================
    await query.edit_message_text("⚠️ زر غير معروف")
