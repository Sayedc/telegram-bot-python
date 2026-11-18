import asyncio
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

# ==========================
# HANDLERS
# ==========================
from handlers.start import start
from handlers.message import handle_message
from handlers.callback import callback_handler
from handlers.errors import error_handler

from handlers.admin import (
    admin_stats,
    admin_top,
    broadcast_cmd,
    users_cmd,
    clear_cmd,
    backup_cmd,
    block_user_cmd,
    unblock_user_cmd,
    admin_metrics_cmd,
)

# ==========================
# CONFIG
# ==========================
from config import BOT_TOKEN, DOWNLOADS_PATH, ADMIN_IDS, LOGS_PATH
from services.common import cleanup_stale

# ==========================
# CORE SYSTEM
# ==========================
from core import metrics, rate_limiter, is_admin, get_uptime


SIGNATURE = "✨ ✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨ ✨"
START_TIME = datetime.now()


def setup_logging():
    """
    Console logging + logs/errors.log (what the admin "سجل الأخطاء" button reads;
    nothing used to write that file).
    """
    os.makedirs(LOGS_PATH, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        os.path.join(LOGS_PATH, "errors.log"),
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # httpx logs every request URL at INFO level, and Telegram URLs contain the
    # bot token -> it would end up in your Railway/Docker logs.
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


async def _periodic_cleanup():
    """Remove leftovers of crashed/aborted downloads every 30 minutes."""
    while True:
        await asyncio.sleep(1800)
        try:
            removed = cleanup_stale(DOWNLOADS_PATH, max_age=3600)
            if removed:
                print(f"🧹 Removed {removed} stale download item(s)", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ Cleanup failed: {exc}", flush=True)


async def post_init(app):
    me = await app.bot.get_me()
    print(f"🤖 BOT: @{me.username}", flush=True)

    # Nothing is downloading yet, so everything left in downloads/ is garbage.
    cleanup_stale(DOWNLOADS_PATH, max_age=0)

    app.bot_data["cleanup_task"] = asyncio.get_running_loop().create_task(
        _periodic_cleanup()
    )


async def post_shutdown(app):
    task = app.bot_data.get("cleanup_task")
    if task:
        task.cancel()


def validate_config():
    """Fail early with a clear message when required configuration is missing."""
    if not BOT_TOKEN or not isinstance(BOT_TOKEN, str) or not BOT_TOKEN.strip():
        raise RuntimeError(
            "BOT_TOKEN is missing. Set it in your environment/config before starting."
        )

    if not DOWNLOADS_PATH or not isinstance(DOWNLOADS_PATH, str):
        raise RuntimeError("DOWNLOADS_PATH is missing or invalid.")

    os.makedirs(DOWNLOADS_PATH, exist_ok=True)

    if not isinstance(ADMIN_IDS, (list, tuple, set)):
        raise RuntimeError("ADMIN_IDS must be a list, tuple, or set of Telegram user IDs.")


def main():
    try:
        validate_config()
        setup_logging()

        # Initialize the database before accepting updates.
        from database.user_repository import init_db
        init_db()

        # concurrent_updates: without it PTB handles ONE update at a time, so a
        # single long download made the bot unresponsive for every other user.
        app = (
            Application.builder()
            .token(BOT_TOKEN.strip())
            .concurrent_updates(True)
            .post_init(post_init)
            .post_shutdown(post_shutdown)
            .build()
        )

        # USER
        app.add_handler(CommandHandler("start", start))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

        # CALLBACK
        app.add_handler(CallbackQueryHandler(callback_handler))

        # ADMIN
        app.add_handler(CommandHandler("stats", admin_stats))
        app.add_handler(CommandHandler("top", admin_top))
        app.add_handler(CommandHandler("broadcast", broadcast_cmd))
        app.add_handler(CommandHandler("users", users_cmd))
        app.add_handler(CommandHandler("clear", clear_cmd))
        app.add_handler(CommandHandler("backup", backup_cmd))
        app.add_handler(CommandHandler("block", block_user_cmd))
        app.add_handler(CommandHandler("unblock", unblock_user_cmd))
        app.add_handler(CommandHandler("metrics", admin_metrics_cmd))

        # ERROR HANDLER
        app.add_error_handler(error_handler)

        print("=" * 50, flush=True)
        print(f"📁 DOWNLOADS_PATH: {os.path.abspath(DOWNLOADS_PATH)}", flush=True)
        print("🗄️ DATABASE: initialized", flush=True)
        print("🚀 STATUS: starting polling", flush=True)
        print("=" * 50, flush=True)

        # Keep the normal polling behavior; do not silently discard pending updates.
        app.run_polling()

    except KeyboardInterrupt:
        print("🛑 Bot stopped manually.", flush=True)
    except Exception as exc:
        print(f"❌ BOT STARTUP/RUNTIME ERROR: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    main()
