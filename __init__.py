# handlers/__init__.py
from .start import start
from .message import handle_message
from .callback import callback_handler
from .admin import (
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
from .download import handle_download
from .errors import error_handler
from .settings import settings_menu, set_quality
from .user import user_profile, user_stats
