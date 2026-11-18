# utils/texts.py
"""
القاموس المركزي لكل نصوص البوت.

* كل الرسائل بتتبعت بـ parse_mode="HTML".
* أي قيمة جاية من مستخدم أو من منصة (اسم، عنوان فيديو، رابط) لازم تعدّي على esc().
* تيليجرام مبيسمحش للبوتات بتغيير حجم الخط، فالتدرّج البصري هنا بيتعمل بالعنوان
  العريض <b> + الاقتباس <blockquote> + الخط الثابت <code> + الفواصل.
"""

import html

BRAND = "Alhawy Downloader"
BOT_HANDLE = "@TheAlhawy_Bot"
DEVELOPER = "@ALHAWY1"
SEP = "━━━━━━━━━━━━━━"

MODE_LABEL = {"video": "فيديو", "audio": "صوت (MP3)"}
MODE_ICON = {"video": "🎬", "audio": "🎵"}


def esc(value):
    """Escape text for Telegram HTML."""
    return html.escape(str(value if value is not None else ""), quote=False)


def _title(icon, text):
    return f"<b>{icon} {text}</b>\n{SEP}"


def short(text, limit=80):
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


# =========================================================
# الترحيب والمساعدة
# =========================================================

def welcome(name):
    return (
        f"<b>مرحباً {esc(name)} 👋</b>\n"
        f"أهلاً بك في <b>{BRAND}</b>\n"
        "أداتك السريعة لتحميل الفيديو والصوت بجودة عالية.\n\n"
        f"{_title('📌', 'المنصات المدعومة')}\n"
        "YouTube  •  TikTok  •  Instagram\n"
        "Facebook  •  X (Twitter)  •  SoundCloud\n"
        "وغيرها من المنصات المدعومة\n\n"
        f"{_title('🚀', 'طريقة الاستخدام')}\n"
        "1️⃣  أرسل رابط المحتوى\n"
        "2️⃣  انتظر لحظات أثناء المعالجة\n"
        "3️⃣  استلم الملف جاهزاً\n\n"
        "<blockquote>استخدم القائمة أسفل الشاشة لاختيار نوع التحميل "
        "(فيديو / صوت) أو لتغيير الجودة.</blockquote>"
    )


def help_text():
    return (
        f"{_title('❓', 'المساعدة')}\n"
        "<b>التحميل</b>\n"
        "أرسل الرابط مباشرة في المحادثة وسيصلك الملف.\n\n"
        "<b>نوع التحميل</b>\n"
        "🎬 <b>تحميل فيديو</b> — ملف MP4\n"
        "🎵 <b>تحميل صوت</b> — ملف MP3\n\n"
        "<b>الجودة</b>\n"
        "⚡ من زر <b>الجودة</b> اختر من 144p إلى 1080p.\n\n"
        "<b>ملاحظات</b>\n"
        "• الحد الأقصى للإرسال 49 ميجابايت، والملفات الأكبر تُضغط تلقائياً.\n"
        "• المحتوى الخاص أو المحذوف لا يمكن تحميله.\n"
        "• لا يدعم البوت البث المباشر.\n\n"
        f"<blockquote>للدعم الفني تواصل مع المطور {DEVELOPER}</blockquote>"
    )


# =========================================================
# الجودة والإعدادات
# =========================================================

def quality_menu(quality, mode):
    return (
        f"{_title('⚡', 'جودة التحميل')}\n"
        f"الجودة الحالية: <b>{esc(quality)}p</b>\n"
        f"النمط الحالي: <b>{MODE_ICON[mode]} {MODE_LABEL[mode]}</b>\n\n"
        "اختر الجودة المناسبة:\n"
        "<blockquote>كلما ارتفعت الجودة زاد حجم الملف. "
        "الملفات التي تتجاوز 49 ميجابايت تُضغط تلقائياً قبل الإرسال.</blockquote>"
    )


def quality_saved(quality):
    return (
        f"✅ <b>تم حفظ الجودة: {esc(quality)}p</b>\n"
        "سيتم تطبيقها على التحميلات القادمة.\n\n"
        "<blockquote>أرسل الرابط الآن لبدء التحميل.</blockquote>"
    )


def settings_menu(settings):
    mode = settings["mode"]
    return (
        f"{_title('⚙️', 'الإعدادات')}\n"
        f"{MODE_ICON[mode]} النمط: <b>{MODE_LABEL[mode]}</b>\n"
        f"⚡ الجودة: <b>{esc(settings['quality'])}p</b>\n\n"
        "اختر ما تريد تعديله:"
    )


def mode_saved(mode, quality):
    if mode == "audio":
        body = "سيتم تحويل أي رابط ترسله إلى ملف <b>MP3</b>."
    else:
        body = f"سيتم تحميل أي رابط ترسله كفيديو بجودة <b>{esc(quality)}p</b>."
    return (
        f"✅ <b>تم تفعيل نمط {MODE_ICON[mode]} {MODE_LABEL[mode]}</b>\n"
        f"{body}\n\n"
        "<blockquote>أرسل الرابط الآن.</blockquote>"
    )


def privacy():
    return (
        f"{_title('🔒', 'سياسة الخصوصية')}\n"
        "<b>البيانات التي نحتفظ بها</b>\n"
        "• معرّف الحساب واسم المستخدم\n"
        "• تاريخ الانضمام وعدد التحميلات\n"
        "• تفضيلاتك (الجودة والنمط)\n\n"
        "<b>الروابط والملفات</b>\n"
        "تتم معالجة الرابط لتنزيل الملف فقط، ثم يُحذف الملف من السيرفر "
        "فور إرساله إليك.\n\n"
        "<b>حذف بياناتك</b>\n"
        "يمكنك حذف كل بياناتك في أي وقت من الإعدادات ← حذف بياناتي."
    )


def delete_data_confirm():
    return (
        f"{_title('🗑️', 'حذف البيانات')}\n"
        "سيتم حذف جميع بياناتك المحفوظة نهائياً، بما فيها إحصائياتك وتفضيلاتك.\n\n"
        "<b>هل أنت متأكد؟</b>"
    )


DATA_DELETED = "✅ <b>تم حذف بياناتك بنجاح.</b>"
DATA_NOT_FOUND = "ℹ️ لا توجد بيانات محفوظة لحسابك."
ACTION_CANCELLED = "✖️ تم إلغاء العملية."


def share(bot_username):
    return (
        f"{_title('📤', 'مشاركة البوت')}\n"
        "ساعد أصدقاءك في الوصول إلى البوت:\n"
        f"<code>https://t.me/{esc(bot_username)}</code>"
    )


SHARE_TEXT = "بوت سريع لتحميل الفيديو والصوت من أشهر المنصات"


def stats(user_stats, joined):
    if not user_stats:
        return (
            f"{_title('📊', 'إحصائياتك')}\n"
            "لا توجد بيانات بعد.\n"
            "<blockquote>أرسل أول رابط لتبدأ.</blockquote>"
        )
    return (
        f"{_title('📊', 'إحصائياتك')}\n"
        f"📥 إجمالي التحميلات:  <b>{user_stats.get('downloads', 0)}</b>\n"
        f"🎬 فيديو:  <b>{user_stats.get('videos', 0)}</b>\n"
        f"🎵 صوت:  <b>{user_stats.get('audio', 0)}</b>\n"
        f"🗓️ عدد الزيارات:  <b>{user_stats.get('visits', 0)}</b>\n"
        f"📅 تاريخ الانضمام:  <b>{esc(str(joined)[:10])}</b>"
    )


# =========================================================
# رسائل عامة
# =========================================================

NO_LINK = (
    "⚠️ <b>لم أجد رابطاً في رسالتك.</b>\n"
    "أرسل رابطاً صالحاً من إحدى المنصات المدعومة."
)
BLOCKED = "🚫 <b>تم تقييد وصولك إلى البوت.</b>\nللاستفسار تواصل مع المطور " + DEVELOPER
INVALID_LINK = "⚠️ <b>الرابط غير صالح أو غير مسموح به.</b>"
UNEXPECTED_ERROR = "⚠️ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى بعد قليل."
UNKNOWN_BUTTON = "هذا الزر لم يعد متاحاً. استخدم القائمة بالأسفل."
NOT_AUTHORIZED = "🚫 غير مصرح لك بهذا الإجراء."


def rate_limited(wait):
    return (
        "⏳ <b>أرسلت عدداً كبيراً من الروابط.</b>\n"
        f"يرجى الانتظار <b>{int(wait)}</b> ثانية ثم المحاولة مجدداً."
    )


# =========================================================
# حالة التحميل
# =========================================================

def status_processing(platform, audio, quality):
    mode = "audio" if audio else "video"
    detail = "MP3" if audio else f"{esc(quality)}p"
    return (
        f"<b>⏳ جارٍ المعالجة…</b>\n"
        f"📱 {esc(platform)}  •  {MODE_ICON[mode]} {detail}"
    )


STATUS_QUEUED = (
    "<b>🕒 طلبك في قائمة الانتظار</b>\n"
    "<blockquote>سيبدأ التحميل تلقائياً فور توفر مكان.</blockquote>"
)


def status_compress(step, total, size_mb, kind="الفيديو"):
    return (
        f"<b>🗜️ جارٍ ضغط {kind}…</b>\n"
        f"المرحلة {step} من {total}  •  الحجم الحالي {size_mb:.1f} MB"
    )


def status_uploading(size_mb):
    return f"<b>📤 جارٍ إرسال الملف…</b>\n📦 الحجم: {size_mb:.1f} MB"


def download_failed(message):
    return f"<b>❌ تعذر إتمام التحميل</b>\n{esc(message)}"


FILE_MISSING = "<b>❌ تعذر إتمام التحميل</b>\nلم يتم العثور على الملف بعد التنزيل."
TOO_BIG_PHOTOS = "<b>❌ تعذر الإرسال</b>\nحجم ملف الصور أكبر من الحد المسموح (49 MB)."
TOO_BIG_AFTER_COMPRESS = (
    "<b>❌ الملف كبير جداً</b>\n"
    "لم يمكن تصغيره إلى الحد المسموح (49 MB). جرّب جودة أقل مثل 480p أو 360p."
)
PREPARE_FAILED = "<b>❌ تعذر تجهيز الملف للإرسال.</b>"
SEND_FAILED = "<b>❌ حدث خطأ أثناء الإرسال</b>\nيرجى المحاولة مرة أخرى."


def caption_video(title, platform, quality, size_mb):
    return (
        f"<b>{esc(short(title, 90))}</b>\n\n"
        f"📱 {esc(platform)}  •  🎞️ {esc(quality)}p  •  📦 {size_mb:.1f} MB\n"
        f"<i>{BRAND}</i> — {BOT_HANDLE}"
    )


def caption_audio(title, platform, size_mb):
    return (
        f"<b>{esc(short(title, 90))}</b>\n\n"
        f"📱 {esc(platform)}  •  🎧 MP3  •  📦 {size_mb:.1f} MB\n"
        f"<i>{BRAND}</i> — {BOT_HANDLE}"
    )


def caption_photos(count, size_mb):
    return (
        f"<b>🖼️ صور منشور TikTok</b>\n\n"
        f"عدد الصور: {esc(count)}  •  📦 {size_mb:.1f} MB\n"
        f"<i>{BRAND}</i> — {BOT_HANDLE}"
    )


# =========================================================
# أخطاء التحميل (تُستخدم من services/common.py)
# =========================================================

DOWNLOAD_ERRORS = {
    "COOKIES_REQUIRED": "🔐 طلبت المنصة تسجيل الدخول أو منعت الطلب مؤقتاً. يرجى المحاولة لاحقاً.",
    "AGE_RESTRICTED": "🔞 هذا المحتوى مقيّد بالعمر ولا يمكن تحميله.",
    "PRIVATE_VIDEO": "🔒 هذا المحتوى خاص. أرسل رابط محتوى عام.",
    "VIDEO_UNAVAILABLE": "🚫 المحتوى غير متاح أو محذوف أو محجوب في بلد السيرفر.",
    "RATE_LIMIT": "⏳ المنصة تحدّ من عدد الطلبات حالياً. يرجى المحاولة بعد قليل.",
    "IP_BLOCKED": "🌐 رفضت المنصة الطلب مؤقتاً (403). يرجى المحاولة لاحقاً.",
    "INVALID_URL": "⚠️ الرابط غير صحيح أو أن المنصة غير مدعومة.",
    "EXTRACTOR_BROKEN": "🛠️ طرأ تغيير على المنصة ويجري تحديث البوت. يرجى المحاولة لاحقاً.",
    "FFMPEG_MISSING": "🎬 خلل تقني في السيرفر. تم إبلاغ الدعم الفني.",
    "LIVE": "🔴 البث المباشر غير مدعوم. أعد المحاولة بعد انتهائه.",
    "TOO_LARGE": "📦 حجم الملف كبير جداً للتحميل. جرّب جودة أقل.",
    "TIMEOUT": "⌛ استغرق التحميل وقتاً أطول من المسموح. جرّب جودة أقل أو رابطاً آخر.",
    "NO_FORMATS": "😕 لم أجد صيغة تحميل مناسبة لهذا المحتوى. جرّب جودة مختلفة.",
    "NO_VIDEO": "🖼️ هذا المنشور لا يحتوي على فيديو (صور فقط).",
    "FILE_NOT_FOUND": "📁 انتهى التحميل لكن الملف غير موجود. يرجى المحاولة مرة أخرى.",
    "DOWNLOAD_ERROR": "⚠️ تعذر التحميل. تأكد من الرابط وحاول مرة أخرى بعد قليل.",
}


# =========================================================
# لوحة الأدمن
# =========================================================

def admin_panel():
    return (
        f"{_title('👑', 'لوحة التحكم')}\n"
        "اختر الإجراء المطلوب:"
    )


def admin_stats(stats, uptime):
    return (
        f"{_title('📊', 'إحصائيات البوت')}\n"
        f"👥 المستخدمون:  <b>{stats['total_users']}</b>\n"
        f"🚫 المقيّدون:  <b>{stats['blocked_users']}</b>\n"
        f"📥 إجمالي التحميلات:  <b>{stats['total_downloads']}</b>\n"
        f"⏱️ مدة التشغيل:  <b>{esc(uptime)}</b>"
    )


def admin_metrics(summary):
    return (
        f"{_title('📈', 'مقاييس الأداء')}\n"
        f"⚡ متوسط الاستجابة:  <b>{summary['avg_response']}s</b>\n"
        f"📥 متوسط زمن التحميل:  <b>{summary['avg_download']}s</b>\n"
        f"✅ نسبة النجاح:  <b>{summary['success_rate']}%</b>\n"
        f"🏆 أكثر منصة:  <b>{esc(summary['top_platform'])}</b>\n"
        f"⚠️ أكثر خطأ:  <b>{esc(summary['common_error'])}</b>"
    )


def admin_top(rows):
    if not rows:
        return f"{_title('🏆', 'الأكثر نشاطاً')}\nلا يوجد مستخدمون بعد."
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = []
    for i, (uid, info) in enumerate(rows, 1):
        mark = "🚫" if info.get("blocked") else "✅"
        lines.append(
            f"{medals.get(i, f'{i}.')} <b>{esc(info.get('name', 'Unknown'))}</b>  {mark}\n"
            f"     <code>{esc(uid)}</code>  •  {info.get('downloads', 0)} تحميل"
        )
    return f"{_title('🏆', 'الأكثر نشاطاً')}\n" + "\n".join(lines)


ADMIN_BROADCAST_PROMPT = (
    f"{_title('📢', 'إعلان للجميع')}\n"
    "أرسل الآن نص الإعلان وسيصل إلى جميع المستخدمين.\n"
    "<blockquote>اكتب «إلغاء» للتراجع.</blockquote>"
)
ADMIN_BLOCK_PROMPT = "🚫 أرسل <b>ID</b> المستخدم الذي تريد تقييده، أو اكتب «إلغاء»."
ADMIN_UNBLOCK_PROMPT = "🔓 أرسل <b>ID</b> المستخدم الذي تريد رفع التقييد عنه، أو اكتب «إلغاء»."
ADMIN_DELETE_ALL_CONFIRM = (
    f"{_title('⚠️', 'تحذير')}\n"
    "سيتم حذف <b>جميع المستخدمين</b> من قاعدة البيانات ولا يمكن التراجع.\n"
    "<blockquote>يُفضّل أخذ نسخة احتياطية أولاً.</blockquote>\n"
    "<b>هل أنت متأكد؟</b>"
)


# =========================================================
# أدوات TikTok (حذف الريبوستات)
# =========================================================

REPOST_INTRO = (
    f"{_title('🧰', 'حذف ريبوستات TikTok')}\n"
    "ستحذف هذه الأداة <b>جميع الريبوستات</b> من حسابك.\n\n"
    "<b>كيف تعمل؟</b>\n"
    "يُطلب منك مسح رمز QR من تطبيق TikTok لتسجيل الدخول. "
    "يتم تسجيل الدخول مؤقتاً على سيرفر البوت لتنفيذ الحذف فقط، "
    "وتُغلق الجلسة فور انتهاء العملية.\n\n"
    "<blockquote>قد تستغرق العملية وقتاً حسب عدد الريبوستات.</blockquote>\n"
    "<b>هل تريد المتابعة؟</b>"
)
REPOST_BUSY = "⏳ توجد عملية جارية على حسابك. يرجى الانتظار حتى تنتهي."
REPOST_PREPARING = "<b>🔄 جارٍ تجهيز تسجيل الدخول…</b>"
REPOST_QR_FAILED = "<b>❌ تعذر تجهيز رمز QR</b>\nيرجى المحاولة لاحقاً."
REPOST_QR_CAPTION = (
    f"{_title('📱', 'تسجيل الدخول إلى TikTok')}\n"
    "1️⃣  افتح تطبيق TikTok\n"
    "2️⃣  اذهب إلى <b>الملف الشخصي</b> ثم <b>رمز QR</b>\n"
    "3️⃣  امسح الرمز الظاهر في الصورة\n\n"
    "<blockquote>أمامك 3 دقائق لإتمام الخطوة.</blockquote>"
)
REPOST_WAITING = "<b>⏳ بانتظار تسجيل الدخول…</b>"
REPOST_TIMEOUT = (
    "<b>⌛ انتهت المهلة</b>\n"
    "لم يتم تسجيل الدخول في الوقت المحدد. يمكنك المحاولة مرة أخرى."
)
REPOST_LOGGED_IN = (
    "<b>✅ تم تسجيل الدخول</b>\n"
    "جارٍ حذف الريبوستات… قد يستغرق ذلك بعض الوقت."
)


def repost_done(count):
    return f"<b>✅ اكتملت العملية</b>\n🗑️ عدد الريبوستات المحذوفة: <b>{esc(count)}</b>"


def repost_failed(error):
    return (
        "<b>❌ تعذر إتمام الحذف</b>\n"
        f"{esc(error)}\n"
        "<blockquote>يرجى المحاولة مرة أخرى لاحقاً.</blockquote>"
    )
