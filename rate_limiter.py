Enter# rate_limiter.py - التحكم في عدد الطلبات
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests  # 10 طلبات
        self.time_window = time_window     # في 60 ثانية
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id):
        """التحقق إذا كان المستخدم مسموح له بالطلب"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        
        # تنظيف الطلبات القديمة
        self.requests[user_id] = [t for t in self.requests[user_id] if t > cutoff]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False, len(self.requests[user_id])
        
        self.requests[user_id].append(now)
        return True, self.max_requests - len(self.requests[user_id])
    
    def get_remaining(self, user_id):
        """عدد الطلبات المتبقية للمستخدم"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        self.requests[user_id] = [t for t in self.requests[user_id] if t > cutoff]
        return max(0, self.max_requests - len(self.requests[user_id]))
