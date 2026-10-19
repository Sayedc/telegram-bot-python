import os
import sys
from datetime import datetime

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
from config import BOT_TOKEN, DOWNLOADS_PATH, ADMIN_IDS

# ==========================
# CORE SYSTEM
# ==========================
from core import metrics, rate_limiter, is_admin, get_uptime


BOT_USERNAME = "@SK_Download_bot"
SIGNATURE = "✨ ✨ 𝓐𝓵𝓱𝓪𝔀𝔂 ✨ ✨"
START_TIME = datetime.now()


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

        # Initialize the database before accepting updates.
        from database.user_repository import init_db
        init_db()

        app = Application.builder().token(BOT_TOKEN.strip()).build()

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
        print(f"🤖 BOT: {BOT_USERNAME}", flush=True)
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
