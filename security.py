Enter# security.py - فحص الأمان والحظر التلقائي
import re
from datetime import datetime, timedelta

SUSPICIOUS_DOMAINS = [
    "malware", "phishing", "fake", "scam", "hack",
    "cryptocurrency", "bitcoin", "mining"
]

BLOCKED_DOMAINS = []  # هتتحدث تلقائياً
FAILED_ATTEMPTS = {}  # تتبع محاولات الفشل

def is_safe_url(url):
    """فحص الرابط قبل التحميل"""
    url_lower = url.lower()
    
    # فحص النطاقات المشبوهة
    for suspicious in SUSPICIOUS_DOMAINS:
        if suspicious in url_lower:
            return False, f"النطاق {suspicious} مشبوه"
    
    # فحص النطاقات المحظورة
    for blocked in BLOCKED_DOMAINS:
        if blocked in url_lower:
            return False, f"النطاق {blocked} محظور"
    
    return True, "آمن"

def record_failed_attempt(user_id, url):
    """تسجيل محاولة فاشلة"""
    now = datetime.now()
    if user_id not in FAILED_ATTEMPTS:
        FAILED_ATTEMPTS[user_id] = []
    
    FAILED_ATTEMPTS[user_id].append({"time": now, "url": url})
    
    # حذف المحاولات القديمة (أكثر من ساعة)
    FAILED_ATTEMPTS[user_id] = [a for a in FAILED_ATTEMPTS[user_id] if now - a["time"] < timedelta(hours=1)]
    
    # إذا تجاوز 10 محاولات فاشلة في الساعة
    if len(FAILED_ATTEMPTS[user_id]) > 10:
        return True  # يحتاج حظر
    return False
