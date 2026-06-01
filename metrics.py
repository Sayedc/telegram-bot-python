here# metrics.py - جمع مقاييس الأداء
import time
from datetime import datetime, timedelta
from collections import defaultdict

class Metrics:
    def __init__(self):
        self.response_times = []
        self.download_times = []
        self.errors = defaultdict(int)
        self.platform_counts = defaultdict(int)
    
    def record_response(self, seconds):
        self.response_times.append(seconds)
        if len(self.response_times) > 100:
            self.response_times.pop(0)
    
    def record_download(self, seconds, platform):
        self.download_times.append(seconds)
        self.platform_counts[platform] += 1
        if len(self.download_times) > 100:
            self.download_times.pop(0)
    
    def record_error(self, error_type):
        self.errors[error_type] += 1
    
    def get_summary(self):
        avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        avg_download = sum(self.download_times) / len(self.download_times) if self.download_times else 0
        success_rate = (sum(self.platform_counts.values()) / (sum(self.platform_counts.values()) + sum(self.errors.values()))) * 100 if (sum(self.platform_counts.values()) + sum(self.errors.values())) > 0 else 100
        
        return {
            "avg_response": round(avg_response, 2),
            "avg_download": round(avg_download, 2),
            "success_rate": round(success_rate, 1),
            "top_platform": max(self.platform_counts, key=self.platform_counts.get) if self.platform_counts else "None",
            "common_error": max(self.errors, key=self.errors.get) if self.errors else "None"
        }
