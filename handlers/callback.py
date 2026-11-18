# handlers/callback.py
import io
import os
import sys
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from keyboards.main_keyboard import (
    main_keyboard,
    admin_keyboard,
    admin_panel,
    quality_keyboard,
    settings_keyboard,
    confirm_keyboard,
)
from database.user_repository import (
    get_user_stats,
    get_all_users,
    delete_user_data,
    load_data,
    save_data,
    get_admin_stats,
    DB_FILE,
)
from config import ADMIN_IDS, SIGNATURE, DOWNLOADS_PATH
from services.common import cleanup_stale
from core import metrics, get_uptime
from utils.constants import SUCCESS_TEXTS, ERROR_TEXTS
from handlers.settings import set_user_quality


# SIGNATURE contains '_' (@TheAlhawy_Bot): escape it wherever parse_mode=Markdown is used.
SIGNATURE_MD = escape_markdown(SIGNATURE)


def is_admin(user_id: int):
    return user_id in ADMIN_IDS


def _restart_process():
    """Restart the bot in place (works on any host, unlike exit code 0 which
    Railway/Docker restart policies treat as a normal shutdown)."""
    try:
        sys.stdout.flush()
        sys.stderr.flush()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception:  # noqa: BLE001
        os._exit(1)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المعالج الرئيسي لكل الأزرار"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # =========================
    # الأزرار الأساسية
    # =========================
    if data == "help_video":
        context.user_data["audio"] = False

        await query.edit_message_text(
            "🎬 تم تفعيل وضع الفيديو.\n\n"
            "📥 أرسل أي رابط الآن وسيتم تحميل الفيديو.",
        )

    elif data == "help_audio":
        context.user_data["audio"] = True

        await query.edit_message_text(
            "🎵 تم تفعيل وضع استخراج الصوت.\n\n"
            "📥 أرسل أي رابط الآن وسيتم تحميله كملف MP3.\n\n"
            "🔄 سيظل الوضع مفعلًا حتى تختار تحميل الفيديو.",
        )

    elif data == "quality_menu":
        await query.edit_message_text(
            "⚡ *اختر الجودة المناسبة:*\n\n📱 الجودة العالية = حجم أكبر\n📱 الجودة المنخفضة = حجم أصغر",
            parse_mode="Markdown",
            reply_markup=quality_keyboard(),
        )

    elif data == "share_bot":
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}"
        await query.edit_message_text(
            f"🎁 *شارك البوت مع أصحابك* 🎁\n\n📤 الرابط:\n`{link}`\n\n🤍 كل ما حد يشترك عبرك بتدعمني",
            parse_mode="Markdown",
        )

    # =========================
    # إحصائيات المستخدم
    # =========================
    elif data == "my_stats":
        stats = get_user_stats(user_id)

        if not stats:
            text = "📊 *إحصائياتك*\n\nلا توجد بيانات بعد 😅\nاستخدم البوت وارجع تاني"
        else:
            text = f"""
📊 *إحصائياتك الشخصية* 📊
━━━━━━━━━━━━━━━━━━━
📥 عدد التحميلات: `{stats.get('downloads', 0)}`
🎬 فيديوهات: `{stats.get('videos', 0)}`
🎵 صوت: `{stats.get('audio', 0)}`
📅 عدد الزيارات: `{stats.get('visits', 0)}`
━━━━━━━━━━━━━━━━━━━
✨ {SIGNATURE_MD} ✨
"""
        await query.edit_message_text(text, parse_mode="Markdown")

    # =========================
    # الإعدادات
    # =========================
    elif data == "settings_menu":
        await query.edit_message_text(
            "⚙️ *الإعدادات* ⚙️\n\nاختر ما تريد تعديله:",
            parse_mode="Markdown",
            reply_markup=settings_keyboard(),
        )

    elif data == "settings_quality":
        await query.edit_message_text(
            "📱 *اختر الجودة الافتراضية:*\n\nاختر الجودة التي تريدها للتحميلات القادمة",
            parse_mode="Markdown",
            reply_markup=quality_keyboard(),
        )

    elif data == "settings_audio":
        context.user_data["audio"] = True
        await query.edit_message_text(
            "🎵 *تم تفعيل وضع الصوت الافتراضي*\n\nسيتم استخراج الصوت تلقائياً من الآن",
            parse_mode="Markdown",
        )

    elif data == "settings_delete_data":
        await query.edit_message_text(
            "🗑️ *هل أنت متأكد من حذف بياناتك؟*\n\nسيتم حذف جميع بياناتك من قاعدة البيانات",
            parse_mode="Markdown",
            reply_markup=confirm_keyboard(),
        )

    elif data == "settings_privacy":
        text = f"""
🔒 *سياسة الخصوصية* 🔒
━━━━━━━━━━━━━━━━━━━
📌 *البيانات المحفوظة:*
• معرف المستخدم
• اسم المستخدم
• تاريخ الانضمام
• عدد التحميلات

🗑️ *مسح البيانات:* من الإعدادات ← مسح بياناتي

📎 الروابط اللي بتبعتها بتتعالج على السيرفر لتنزيل الملف فقط، والملفات بتتمسح بعد الإرسال.

✨ {SIGNATURE_MD} ✨
"""
        await query.edit_message_text(text, parse_mode="Markdown")

    # =========================
    # تأكيدات
    # =========================
    elif data == "confirm_yes":
        if delete_user_data(user_id):
            await query.edit_message_text(
                f"🗑️ تم حذف بياناتك بنجاح\n\n{SIGNATURE}"
            )
        else:
            await query.edit_message_text("❌ *لا توجد بيانات لك*", parse_mode="Markdown")

    elif data == "confirm_no":
        await query.edit_message_text(
            f"✅ *تم إلغاء العملية*\n\n✨ {SIGNATURE_MD} ✨",
            parse_mode="Markdown",
        )

    # =========================
    # لوحة الأدمن
    # =========================
    elif data == "admin_panel":
        if not is_admin(user_id):
            await query.edit_message_text("🚫 *غير مصرح* 🚫\nهذه اللوحة مخصصة للأدمن فقط", parse_mode="Markdown")
            return

        await query.edit_message_text(
            "👑 *لوحة تحكم الأدمن* 👑\n━━━━━━━━━━━━━━━━━━━\nاختر الأمر المناسب:",
            parse_mode="Markdown",
            reply_markup=admin_panel(),
        )

    elif data == "admin_stats":
        if not is_admin(user_id):
            return

        stats = get_admin_stats()

        text = f"""
👑 إحصائيات البوت

━━━━━━━━━━━━━━━━━━

👥 المستخدمين:
{stats["total_users"]}

🚫 المحظورين:
{stats["blocked_users"]}

📥 إجمالي التحميلات:
{stats["total_downloads"]}

━━━━━━━━━━━━━━━━━━

⏱️ وقت التشغيل:
{get_uptime()}

{SIGNATURE}
"""

        await query.edit_message_text(text)

    elif data == "admin_top":
        if not is_admin(user_id):
            return

        users = get_all_users()

        sorted_users = sorted(
            users.items(),
            key=lambda x: x[1].get("downloads", 0),
            reverse=True,
        )[:10]

        if not sorted_users:
            await query.edit_message_text("🏆 لا يوجد مستخدمون بعد.")
            return

        text = "🏆 ترتيب المستخدمين الأكثر نشاطاً\n\n"

        for i, (uid, info) in enumerate(sorted_users, 1):
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."

            status = "🚫" if info.get("blocked") else "✅"
            name = str(info.get("name", "Unknown"))

            text += (
                f"{medal} {name}\n"
                f"ID: {uid}\n"
                f"التحميلات: {info.get('downloads', 0)}\n"
                f"الحالة: {status}\n\n"
            )

        text += SIGNATURE

        await query.edit_message_text(text)

    elif data == "admin_broadcast":
        if not is_admin(user_id):
            return

        context.user_data["admin_state"] = "broadcast"

        await query.edit_message_text(
            "📢 *إرسال إعلان*\n\n"
            "✍️ أرسل الآن الرسالة التي تريد إرسالها لجميع المستخدمين.\n\n"
            "❌ اكتب (إلغاء) للإلغاء.",
            parse_mode="Markdown",
        )

    elif data == "admin_users":
        if not is_admin(user_id):
            return

        users = get_all_users()

        lines = [
            f"{uid} | {info.get('name')} | {info.get('downloads', 0)}"
            for uid, info in users.items()
        ]
        payload = io.BytesIO(("\n".join(lines) or "no users").encode("utf-8"))

        await query.message.reply_document(
            document=payload,
            filename="users.txt",
            caption="👥 قائمة المستخدمين",
        )

    elif data == "admin_block":
        if not is_admin(user_id):
            return

        context.user_data["admin_state"] = "block"

        await query.edit_message_text(
            "🚫 أرسل ID المستخدم الذي تريد حظره.",
            parse_mode="Markdown",
        )

    elif data == "admin_unblock":
        if not is_admin(user_id):
            return

        context.user_data["admin_state"] = "unblock"

        await query.edit_message_text(
            "🔓 أرسل ID المستخدم الذي تريد فك حظره.",
            parse_mode="Markdown",
        )

    elif data == "admin_clear":
        if not is_admin(user_id):
            return

        # Entries younger than 10 minutes may belong to a download in progress.
        count = cleanup_stale(DOWNLOADS_PATH, max_age=600)

        await query.edit_message_text(
            f"🗑️ تم حذف {count} عنصر من الكاش (الأقدم من 10 دقايق)."
        )

    elif data == "admin_delete_all":
        if not is_admin(user_id):
            return

        await query.edit_message_text(
            "⚠️ *تحذير*\n\nده هيمسح *كل المستخدمين* من قاعدة البيانات ومفيش رجوع.\n"
            "خد نسخة احتياطية الأول لو محتاج.\n\nمتأكد؟",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ نعم، احذف الكل", callback_data="admin_delete_all_yes"),
                    InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel"),
                ],
            ]),
        )

    elif data == "admin_delete_all_yes":
        if not is_admin(user_id):
            return

        data_db = load_data()
        admin = data_db["users"].get(str(user_id))

        # Keep the admin's own record only if it exists (it used to store None).
        data_db["users"] = {str(user_id): admin} if admin else {}
        data_db["total"] = len(data_db["users"])
        save_data(data_db)

        await query.edit_message_text(
            "✅ تم حذف جميع المستخدمين."
        )

    elif data == "admin_uptime":
        if not is_admin(user_id):
            return

        await query.edit_message_text(
            f"⏱ وقت التشغيل\n\n{get_uptime()}"
        )

    elif data == "admin_backup":
        if not is_admin(user_id):
            return

        if not os.path.exists(DB_FILE):
            await query.edit_message_text("❌ مفيش قاعدة بيانات لسه.")
            return

        backup = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(DB_FILE, "rb") as src:
            await query.message.reply_document(
                document=src,
                filename=backup,
                caption="📦 Database Backup",
            )

        await query.edit_message_text("✅ تم إرسال النسخة الاحتياطية")

    elif data == "admin_metrics":
        if not is_admin(user_id):
            return

        summary = metrics.get_summary()

        text = f"""
📊 مقاييس الأداء

━━━━━━━━━━━━━━

⚡ متوسط الاستجابة:
{summary['avg_response']} ثانية

📥 متوسط التحميل:
{summary['avg_download']} ثانية

✅ نسبة النجاح:
{summary['success_rate']}%

🏆 أكثر منصة:
{summary['top_platform']}

━━━━━━━━━━━━━━

{SIGNATURE}
"""

        await query.edit_message_text(text)

    elif data == "admin_logs":
        if not is_admin(user_id):
            return

        log_file = os.path.join("logs", "errors.log")

        if not os.path.exists(log_file):
            await query.edit_message_text("لا يوجد سجل أخطاء.")
            return

        with open(log_file, "r", encoding="utf8", errors="replace") as f:
            logs = f.readlines()[-10:]

        text = "".join(logs)[-3500:] or "السجل فاضي."
        await query.edit_message_text("آخر الأخطاء:\n\n" + text)

    elif data == "admin_restart":
        if not is_admin(user_id):
            return

        await query.edit_message_text("🔄 جاري إعادة تشغيل البوت...\n\n⏳ سيستغرق بضع ثوانٍ")
        _restart_process()

    # =========================
    # حذف ريبوستات تيك توك (جديد)
    # =========================
    elif data == "delete_reposts":
        await query.edit_message_text(
            "⚠️ *حذف ريبوستات تيك توك*\n\n"
            "🗑️ هذه الميزة ستحذف *كل الريبوستات* من حسابك.\n\n"
            "🔐 هنطلب منك تسجيل دخول عن طريق QR Code.\n"
            "⚠️ التسجيل بيتم على سيرفر البوت بشكل مؤقت لتنفيذ الحذف، والجلسة بتتقفل أول ما العملية تخلص.\n\n"
            "⚠️ *ملاحظة:* الحذف ممكن ياخد وقت على حسب عدد الريبوستات.\n\n"
            "هل أنت متأكد؟",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ نعم، متأكد", callback_data="confirm_delete_reposts"),
                    InlineKeyboardButton("❌ إلغاء", callback_data="back"),
                ],
            ]),
        )

    elif data == "confirm_delete_reposts":
        from services.tiktok_repost import repost_manager

        # A double tap used to start two browsers and leak the first one.
        if context.user_data.get("repost_busy"):
            await query.message.reply_text("⏳ في عملية جارية بالفعل على حسابك. استنى تخلص.")
            return

        context.user_data["repost_busy"] = True

        try:
            await query.edit_message_text("🔄 جاري تجهيز تسجيل الدخول...")

            qr_path = await repost_manager.start_login(user_id)

            if not qr_path or not os.path.exists(qr_path):
                await query.edit_message_text(
                    "❌ فشل تجهيز QR Code.\n\n"
                    "💡 حاول مرة أخرى لاحقاً."
                )
                return

            with open(qr_path, "rb") as f:
                await query.message.reply_photo(
                    photo=f,
                    caption=(
                        "📱 *تسجيل دخول تيك توك*\n\n"
                        "1️⃣ افتح تطبيق تيك توك على تليفونك\n"
                        "2️⃣ روح لـ *البروفايل* ثم اضغط على *QR Code*\n"
                        "3️⃣ امسح الـ QR ده\n\n"
                        "⏳ *في انتظار تسجيل الدخول...*\n"
                        "⏱️ عندك 3 دقايق"
                    ),
                    parse_mode="Markdown",
                )

            await query.message.reply_text("⏳ جاري التحقق من تسجيل الدخول...")

            logged_in = await repost_manager.wait_login(user_id, timeout=180)

            if not logged_in:
                await query.message.reply_text(
                    "❌ *انتهت المهلة*\n\n"
                    "المستخدم لم يسجل دخول في الوقت المحدد.\n"
                    "جرب تاني وأسرع في المسح.",
                    parse_mode="Markdown",
                )
                return

            await query.message.reply_text(
                "✅ *تم تسجيل الدخول بنجاح!*\n\n"
                "🔄 جاري حذف الريبوستات...\n"
                "⏳ العملية ممكن تاخد شوية وقت.",
                parse_mode="Markdown",
            )

            result = await repost_manager.delete_reposts(user_id)

            if result.get("success"):
                await query.message.reply_text(
                    f"✅ *تم الانتهاء!*\n\n"
                    f"🗑️ عدد الريبوستات المحذوفة: `{result.get('deleted', 0)}`\n\n"
                    f"{SIGNATURE_MD}",
                    parse_mode="Markdown",
                )
            else:
                await query.message.reply_text(
                    f"❌ فشل الحذف\n\n"
                    f"⚠️ {result.get('error', 'خطأ غير معروف')}\n\n"
                    f"💡 جرب تاني لاحقاً."
                )

        finally:
            # Always close the browser + virtual display, even after an error.
            context.user_data.pop("repost_busy", None)
            await repost_manager.cleanup(user_id)

    # =========================
    # أزرار الجودة
    # =========================
    elif data.startswith("q_"):
        quality = data.replace("q_", "")

        if quality == "audio":
            context.user_data["audio"] = True
            await query.edit_message_text(
                "🎵 *وضع الصوت مفعل*\n\nسيتم استخراج الصوت من الفيديوهات القادمة",
                parse_mode="Markdown",
            )
        else:
            context.user_data["quality"] = quality
            context.user_data["audio"] = False
            set_user_quality(user_id, quality)
            await query.edit_message_text(
                f"⚡ *تم ضبط الجودة إلى {quality}p*\n\nسيتم استخدام هذه الجودة للتحميلات القادمة",
                parse_mode="Markdown",
            )

    # =========================
    # المساعدة
    # =========================
    elif data == "help":
        text = """
📌 *المساعدة* 📌
━━━━━━━━━━━━━━━━━━━
🎬 *تحميل:* أرسل الرابط مباشرة
🎵 *صوت:* اضغط "استخراج صوت" من القائمة ثم أرسل الرابط
⚡ *جودة:* اختر من القائمة
🗑️ *حذف ريبوستات:* من القائمة الرئيسية
📊 *إحصائياتك:* من القائمة الرئيسية
🎁 *مشاركة:* من القائمة الرئيسية
⚙️ *إعدادات ومسح البيانات:* من القائمة
🔒 *خصوصية:* من الإعدادات

🌍 *البوت بينزل من معظم المواقع*

✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨
"""
        await query.edit_message_text(text, parse_mode="Markdown")

    # =========================
    # رجوع
    # =========================
    elif data == "back":
        kb = admin_keyboard() if is_admin(user_id) else main_keyboard()
        await query.edit_message_text(
            "🖤 *القائمة الرئيسية* 🖤",
            reply_markup=kb,
            parse_mode="Markdown",
        )

    # =========================
    # أي شيء آخر
    # =========================
    else:
        await query.edit_message_text("⚠️ *إجراء غير معروف*\n\nجرب مرة أخرى", parse_mode="Markdown")
