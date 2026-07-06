# handlers/callback.py
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import os
import shutil

from keyboards.main_keyboard import (
    main_keyboard,
    admin_keyboard,
    admin_panel,
    quality_keyboard,
    settings_keyboard,
    confirm_keyboard,
)
from database.user_repository import get_user_stats, get_all_users, delete_user_data, load_data, save_data
from config import ADMIN_IDS, SIGNATURE
from core import downloader, metrics, get_uptime
from utils.constants import SUCCESS_TEXTS, ERROR_TEXTS
from handlers.settings import set_user_quality


def is_admin(user_id: int):
    return user_id in ADMIN_IDS


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
        await query.edit_message_text(
            "🎬 *تحميل فيديو*\n\n📤 أرسل رابط الفيديو مباشرة وسأقوم بتحميله بأعلى جودة\n\n✅ المنصات المدعومة:\n• TikTok (بدون علامة مائية)\n• YouTube\n• Instagram\n• Facebook\n• Twitter\n• وأي موقع تاني",
            parse_mode="Markdown",
        )

    elif data == "help_audio":
        await query.edit_message_text(
            "🎵 *استخراج الصوت*\n\n📤 استخدم الأمر `/audio` ثم أرسل رابط الفيديو\n\n🎧 سأرسل لك ملف MP3 بجودة عالية",
            parse_mode="Markdown",
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
✨ {SIGNATURE} ✨
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

📅 *مدة الحفظ:* 30 يوم
🗑️ *مسح البيانات:* /delete_my_data

🔐 *الأمان:* بياناتك آمنة ومشفرة

✨ {SIGNATURE} ✨
"""
        await query.edit_message_text(text, parse_mode="Markdown")

    # =========================
    # تأكيدات
    # =========================
    elif data == "confirm_yes":
        if delete_user_data(user_id):
            await query.edit_message_text(
                f"🗑️ *تم حذف بياناتك بنجاح*\n\n✨ {SIGNATURE} ✨",
                parse_mode="Markdown",
            )
        else:
            await query.edit_message_text("❌ *لا توجد بيانات لك*", parse_mode="Markdown")

    elif data == "confirm_no":
        await query.edit_message_text(
            "✅ *تم إلغاء العملية*\n\n✨ {SIGNATURE} ✨",
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

        from database.user_repository import get_admin_stats

        stats = get_admin_stats()
        d_stats = downloader.get_stats()

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

⚡ التحميلات النشطة:
{d_stats["active"]}

📋 قائمة الانتظار:
{d_stats["queue_size"]}

✅ الناجحة:
{d_stats["success"]}

❌ الفاشلة:
{d_stats["failed"]}

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
            await query.edit_message_text("🏆 *لا يوجد مستخدمين بعد*", parse_mode="Markdown")
            return

        text = "🏆 *ترتيب المستخدمين الأكثر نشاطاً* 🏆\n━━━━━━━━━━━━━━━━━━━\n"
        for i, (uid, info) in enumerate(sorted_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}️⃣"
            status = "🚫" if info.get("blocked") else "✅"
            name = info.get("name") or "No Username"

            text += (
                f"{medal} {name}\n"
                f"🆔 `{uid}`\n"
                f"📥 {info.get('downloads',0)} تحميل\n"
                f"{status}\n\n"
            )

        text += f"\n✨ {SIGNATURE} ✨"
        await query.edit_message_text(text, parse_mode="Markdown")

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

        from database.user_repository import get_all_users
        import os

        users = get_all_users()

        with open("users.txt", "w", encoding="utf-8") as f:
            for uid, info in users.items():
                f.write(
                    f"{uid} | {info.get('name')} | {info.get('downloads', 0)}\n"
                )

        await query.message.reply_document(
            document=open("users.txt", "rb"),
            caption="👥 قائمة المستخدمين"
        )

        os.remove("users.txt")

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

        count = 0

        for file in os.listdir("downloads"):
            path = os.path.join("downloads", file)

            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                count += 1
            except Exception:
                pass

        await query.edit_message_text(
            f"🗑️ تم حذف {count} ملف من الكاش."
        )

    elif data == "admin_delete_all":
        if not is_admin(user_id):
            return

        data_db = load_data()
        admin = data_db["users"].get(str(user_id))

        data_db["users"] = {
            str(user_id): admin
        }
        data_db["total"] = 1
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

        backup = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy("database.json", backup)

        await query.message.reply_document(
            open(backup, "rb"),
            caption="📦 Database Backup"
        )

        os.remove(backup)
        await query.edit_message_text("✅ تم إرسال النسخة الاحتياطية")

    elif data == "admin_metrics":
        if not is_admin(user_id):
            return

        summary = metrics.get_summary()
        stats = downloader.get_stats()

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

📦 Queue:
{stats['queue_size']}

🚀 Active:
{stats['active']}

✅ Success:
{stats['success']}

❌ Failed:
{stats['failed']}

━━━━━━━━━━━━━━

{SIGNATURE}
"""

        await query.edit_message_text(text)

    elif data == "admin_logs":
        if not is_admin(user_id):
            return

        if not os.path.exists("logs/errors.log"):
            await query.edit_message_text("لا يوجد سجل أخطاء.")
            return

        with open("logs/errors.log", "r", encoding="utf8") as f:
            logs = f.readlines()[-10:]

        await query.edit_message_text(
            "آخر الأخطاء:\n\n" + "".join(logs)
        )

    elif data == "admin_restart":
        if not is_admin(user_id):
            return

        await query.edit_message_text("🔄 *جاري إعادة تشغيل البوت...*\n\n⏳ سيستغرق بضع ثوانٍ")
        os._exit(0)

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
🎵 *صوت:* /audio ثم الرابط
⚡ *جودة:* اختر من القائمة
📊 *إحصائيات:* /stats
🎁 *مشاركة:* /share
⚙️ *إعدادات:* من القائمة
🔒 *خصوصية:* /privacy
🗑️ *مسح بياناتي:* /delete_my_data

🌍 *البوت بينزل أي حاجة من أي موقع*

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
