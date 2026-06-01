# security.py - فحص الأمان والحظر التلقائي
import re
from datetime import datetime, timedelta

# قائمة النطاقات المشبوهة (تتحدث تلقائياً)
SUSPICIOUS_DOMAINS = [
    "malware", "phishing", "fake", "scam", "hack",
    "cryptocurrency", "bitcoin", "mining", "porn",
    "adult", "gambling", "casino", "poker", "lottery"
]

# قائمة النطاقات المحظورة (يدوياً)
BLOCKED_DOMAINS = []

# تتبع المحاولات الفاشلة لكل مستخدم
FAILED_ATTEMPTS = {}
BLOCKED_USERS = {}  # {user_id: unblock_time}

def is_safe_url(url):
    """فحص الرابط قبل التحميل"""
    url_lower = url.lower()
    
    # فحص النطاقات المشبوهة
    for suspicious in SUSPICIOUS_DOMAINS:
        if suspicious in url_lower:
            return False, f"⚠️ النطاق '{suspicious}' مشبوه وتم حظره"
    
    # فحص النطاقات المحظورة يدوياً
    for blocked in BLOCKED_DOMAINS:
        if blocked in url_lower:
            return False, f"🚫 النطاق '{blocked}' محظور بواسطة الأدمن"
    
    return True, "آمن"

def record_failed_attempt(user_id, url):
    """تسجيل محاولة فاشلة وتحديد إذا كان يحتاج حظر"""
    now = datetime.now()
    if user_id not in FAILED_ATTEMPTS:
        FAILED_ATTEMPTS[user_id] = []
    
    FAILED_ATTEMPTS[user_id].append({"time": now, "url": url})
    
    # تنظيف المحاولات القديمة (أكثر من ساعة)
    FAILED_ATTEMPTS[user_id] = [a for a in FAILED_ATTEMPTS[user_id] if now - a["time"] < timedelta(hours=1)]
    
    # إذا تجاوز 5 محاولات فاشلة في الساعة → حظر مؤقت
    if len(FAILED_ATTEMPTS[user_id]) >= 5:
        BLOCKED_USERS[user_id] = now + timedelta(minutes=30)
        return True, "تم حظرك مؤقتاً لمدة 30 دقيقة لكثرة المحاولات الفاشلة"
    
    return False, f"تبقى {5 - len(FAILED_ATTEMPTS[user_id])} محاولة قبل الحظر المؤقت"

def is_user_blocked(user_id):
    """التحقق إذا كان المستخدم محظوراً"""
    if user_id in BLOCKED_USERS:
        if datetime.now() < BLOCKED_USERS[user_id]:
            remaining = (BLOCKED_USERS[user_id] - datetime.now()).seconds // 60
            return True, f"أنت محظور مؤقتاً لمدة {remaining} دقيقة"
        else:
            # إلغاء الحظر بعد انتهاء الوقت
            del BLOCKED_USERS[user_id]
            if user_id in FAILED_ATTEMPTS:
                del FAILED_ATTEMPTS[user_id]
    return False, None

def add_blocked_domain(domain):
    """إضافة نطاق إلى القائمة السوداء (للأدمن)"""
    if domain not in BLOCKED_DOMAINS:
        BLOCKED_DOMAINS.append(domain)
        return True
    return False

def remove_blocked_domain(domain):
    """إزالة نطاق من القائمة السوداء"""
    if domain in BLOCKED_DOMAINS:
        BLOCKED_DOMAINS.remove(domain)
        return True
    return False

def get_blocked_domains():
    """الحصول على قائمة النطاقات المحظورة"""
    return BLOCKED_DOMAINS.copy()

def get_failed_stats():
    """إحصائيات المحاولات الفاشلة"""
    return {
        "total_failed": sum(len(attempts) for attempts in FAILED_ATTEMPTS.values()),
        "blocked_users": len(BLOCKED_USERS),
        "active_failures": len(FAILED_ATTEMPTS)
    }
