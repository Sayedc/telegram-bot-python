# metrics.py - مقاييس الأداء والإحصائيات
import time
from datetime import datetime, timedelta
from collections import defaultdict

class Metrics:
    def __init__(self):
        self.response_times = []
        self.download_times = []
        self.errors = defaultdict(int)
        self.platform_counts = defaultdict(int)
        self.user_activity = defaultdict(int)
        self.daily_stats = defaultdict(lambda: {"downloads": 0, "users": set()})
    
    def record_response(self, seconds):
        """تسجيل زمن استجابة البوت"""
        self.response_times.append(seconds)
        if len(self.response_times) > 100:
            self.response_times.pop(0)
    
    def record_download(self, seconds, platform, user_id):
        """تسجيل عملية تحميل"""
        self.download_times.append(seconds)
        self.platform_counts[platform] += 1
        self.user_activity[user_id] += 1
        
        # إحصائيات يومية
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_stats[today]["downloads"] += 1
        self.daily_stats[today]["users"].add(user_id)
        
        if len(self.download_times) > 100:
            self.download_times.pop(0)
    
    def record_error(self, error_type, user_id=None):
        """تسجيل خطأ"""
        self.errors[error_type] += 1
        if user_id:
            self.user_activity[user_id] = self.user_activity.get(user_id, 0) - 1
    
    def get_summary(self):
        """ملخص الأداء"""
        avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        avg_download = sum(self.download_times) / len(self.download_times) if self.download_times else 0
        total_attempts = sum(self.platform_counts.values()) + sum(self.errors.values())
        success_rate = (sum(self.platform_counts.values()) / total_attempts * 100) if total_attempts > 0 else 100
        
        return {
            "avg_response": round(avg_response, 2),
            "avg_download": round(avg_download, 2),
            "success_rate": round(success_rate, 1),
            "top_platform": max(self.platform_counts, key=self.platform_counts.get) if self.platform_counts else "None",
            "common_error": max(self.errors, key=self.errors.get) if self.errors else "None",
            "total_downloads": sum(self.platform_counts.values()),
            "active_users": len([u for u, c in self.user_activity.items() if c > 0])
        }
    
    def get_daily_report(self, days=7):
        """تقرير آخر 7 أيام"""
        report = []
        today = datetime.now()
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self.daily_stats.get(date, {"downloads": 0, "users": set()})
            report.append({
                "date": date,
                "downloads": stats["downloads"],
                "users": len(stats["users"])
            })
        return report
    
    def get_top_users(self, limit=10):
        """أكثر المستخدمين نشاطاً"""
        sorted_users = sorted(self.user_activity.items(), key=lambda x: x[1], reverse=True)
        return sorted_users[:limit]
    
    def reset(self):
        """إعادة تعيين المقاييس (للاختبار)"""
        self.response_times = []
        self.download_times = []
        self.errors = defaultdict(int)
        self.platform_counts = defaultdict(int)
