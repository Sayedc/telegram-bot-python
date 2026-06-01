# rate_limiter.py - التحكم في عدد الطلبات
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        """
        max_requests: الحد الأقصى للطلبات
        time_window: الفترة الزمنية بالثواني
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id):
        """التحقق إذا كان المستخدم مسموح له بالطلب"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        
        # تنظيف الطلبات القديمة
        self.requests[user_id] = [t for t in self.requests[user_id] if t > cutoff]
        
        if len(self.requests[user_id]) >= self.max_requests:
            # حساب وقت الانتظار
            oldest = min(self.requests[user_id])
            wait_time = self.time_window - (now - oldest).total_seconds()
            return False, round(wait_time), 0
        
        self.requests[user_id].append(now)
        remaining = self.max_requests - len(self.requests[user_id])
        return True, 0, remaining
    
    def get_remaining(self, user_id):
        """عدد الطلبات المتبقية للمستخدم"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        self.requests[user_id] = [t for t in self.requests[user_id] if t > cutoff]
        return max(0, self.max_requests - len(self.requests[user_id]))
    
    def get_reset_time(self, user_id):
        """وقت تجديد الطلبات"""
        if user_id not in self.requests or not self.requests[user_id]:
            return 0
        
        oldest = min(self.requests[user_id])
        reset_time = self.time_window - (datetime.now() - oldest).total_seconds()
        return max(0, round(reset_time))
    
    def reset_user(self, user_id):
        """إعادة تعيين طلبات مستخدم معين"""
        if user_id in self.requests:
            del self.requests[user_id]
