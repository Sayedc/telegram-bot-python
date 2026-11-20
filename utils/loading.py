import asyncio

BARS = [
    "▰▱▱▱▱",
    "▰▰▱▱▱",
    "▰▰▰▱▱",
    "▰▰▰▰▱",
    "▰▰▰▰▰",
]

ICONS = {
    "YouTube": "▶️",
    "TikTok": "🎵",
    "Instagram": "📸",
    "Facebook": "📘",
    "Twitter": "🐦",
    "X": "🐦",
    "SoundCloud": "🎧",
}


class LoadingMessage:

    def __init__(self, message, platform="Media"):
        self.message = message
        self.platform = platform
        self.running = True

    async def animate(self):

        step = 0

        while self.running:

            bar = BARS[step]

            icon = ICONS.get(self.platform, "📁")

            text = (
                "━━━━━━━━━━━━━━\n\n"
                "⬇️ جاري التحميل\n\n"
                f"{icon} {self.platform}\n\n"
                f"{bar}\n\n"
                "━━━━━━━━━━━━━━"
            )

            try:
                await self.message.edit_text(text)
            except Exception:
                pass

            step += 1

            if step >= len(BARS):
                step = 0

            await asyncio.sleep(0.6)

    def stop(self):
        self.running = False
