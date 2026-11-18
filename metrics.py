# metrics.py
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
        self.daily_stats = defaultdict(
            lambda: {
                "downloads": 0,
                "users": set()
            }
        )

    def record_response(self, seconds):
        self.response_times.append(seconds)
        if len(self.response_times) > 100:
            self.response_times.pop(0)

    def record_download(self, seconds, platform, user_id):
        self.download_times.append(seconds)
        self.platform_counts[platform] += 1
        self.user_activity[user_id] += 1

        today = datetime.now().strftime("%Y-%m-%d")

        self.daily_stats[today]["downloads"] += 1
        self.daily_stats[today]["users"].add(user_id)

        if len(self.download_times) > 100:
            self.download_times.pop(0)

    def record_error(self, error_type, user_id=None):
        self.errors[error_type] += 1

    def get_summary(self):
        avg_response = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times else 0
        )

        avg_download = (
            sum(self.download_times) / len(self.download_times)
            if self.download_times else 0
        )

        total_downloads = sum(self.platform_counts.values())
        total_errors = sum(self.errors.values())

        total = total_downloads + total_errors

        success_rate = (
            (total_downloads / total) * 100
            if total
            else 100
        )

        return {
            "avg_response": round(avg_response, 2),
            "avg_download": round(avg_download, 2),
            "success_rate": round(success_rate, 1),
            "top_platform": (
                max(self.platform_counts, key=self.platform_counts.get)
                if self.platform_counts else "None"
            ),
            "common_error": (
                max(self.errors, key=self.errors.get)
                if self.errors else "None"
            ),
            "total_downloads": total_downloads,
            "active_users": len(
                [u for u in self.user_activity if self.user_activity[u] > 0]
            ),
        }

    def get_daily_report(self, days=7):
        report = []

        for i in range(days):
            date = (
                datetime.now() - timedelta(days=i)
            ).strftime("%Y-%m-%d")

            stats = self.daily_stats.get(
                date,
                {"downloads": 0, "users": set()}
            )

            report.append({
                "date": date,
                "downloads": stats["downloads"],
                "users": len(stats["users"]),
            })

        return report

    def get_top_users(self, limit=10):
        return sorted(
            self.user_activity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

    def reset(self):
        self.response_times.clear()
        self.download_times.clear()
        self.errors.clear()
        self.platform_counts.clear()
        self.user_activity.clear()
        self.daily_stats.clear()


# ========= مهم =========
metrics = Metrics()
