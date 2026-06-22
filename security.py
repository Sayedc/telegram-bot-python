# security.py - فحص الأمان فقط (بدون حظر مؤقت)

from datetime import datetime, timedelta

# قائمة النطاقات المشبوهة
SUSPICIOUS_DOMAINS = [
    "malware", "phishing", "fake", "scam", "hack",
    "cryptocurrency", "bitcoin", "mining", "porn",
    "adult", "gambling", "casino", "poker", "lottery"
]

# قائمة النطاقات المحظورة يدوياً
BLOCKED_DOMAINS = []

# إحصائيات فقط
FAILED_ATTEMPTS = {}
BLOCKED_USERS = {}

def is_safe_url(url):
    """فحص الرابط قبل التحميل"""
    url_lower = url.lower()

    for suspicious in SUSPICIOUS_DOMAINS:
        if suspicious in url_lower:
            return False, f"⚠️ النطاق '{suspicious}' مشبوه وتم حظره"

    for blocked in BLOCKED_DOMAINS:
        if blocked in url_lower:
            return False, f"🚫 النطاق '{blocked}' محظور بواسطة الأدمن"

    return True, "آمن"

def record_failed_attempt(user_id, url):
    """تسجيل المحاولات الفاشلة فقط بدون حظر"""
    now = datetime.now()

    if user_id not in FAILED_ATTEMPTS:
        FAILED_ATTEMPTS[user_id] = []

    FAILED_ATTEMPTS[user_id].append({
        "time": now,
        "url": url
    })

    FAILED_ATTEMPTS[user_id] = [
        a for a in FAILED_ATTEMPTS[user_id]
        if now - a["time"] < timedelta(hours=1)
    ]

    return False, "لا يوجد حظر مؤقت مفعل"

def is_user_blocked(user_id):
    """إلغاء الحظر المؤقت نهائياً"""
    return False, None

def add_blocked_domain(domain):
    if domain not in BLOCKED_DOMAINS:
        BLOCKED_DOMAINS.append(domain)
        return True
    return False

def remove_blocked_domain(domain):
    if domain in BLOCKED_DOMAINS:
        BLOCKED_DOMAINS.remove(domain)
        return True
    return False

def get_blocked_domains():
    return BLOCKED_DOMAINS.copy()

def get_failed_stats():
    return {
        "total_failed": sum(len(attempts) for attempts in FAILED_ATTEMPTS.values()),
        "blocked_users": 0,
        "active_failures": len(FAILED_ATTEMPTS)
    }
