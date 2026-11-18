import asyncio

from utils.messages import PROGRESS_BAR


class LoadingMessage:

    def __init__(self, message, platform="Unknown"):
        self.message = message
        self.platform = platform
        self.running = True

    async def animate(self):

        step = 0

        stages = [
            "🔗 الاتصال بالخادم...",
            "🔍 تحليل الرابط...",
            "📋 استخراج البيانات...",
            "⬇️ تنزيل الوسائط...",
            "🛠️ تجهيز الملف...",
            "📦 تجهيز الإرسال...",
        ]

        while self.running:

            progress = PROGRESS_BAR[min(step, len(PROGRESS_BAR) - 1)]
            status = stages[min(step, len(stages) - 1)]

            text = (
                "╭────────────────────╮\n\n"
                "🤖 Alhawy Downloader\n\n"
                f"🎬 المنصة: {self.platform}\n\n"
                f"{status}\n\n"
                f"{progress}\n\n"
                "⏳ يرجى عدم إغلاق المحادثة\n\n"
                "╰────────────────────╯"
            )

            try:
                await self.message.edit_text(text)
            except Exception:
                pass

            if step < len(PROGRESS_BAR) - 1:
                step += 1

            await asyncio.sleep(1.2)

    def stop(self):
        self.running = False
