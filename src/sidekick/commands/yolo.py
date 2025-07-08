"""Handle /yolo command."""

from sidekick import ui
from sidekick.session import session


async def handle_yolo():
    """Handle /yolo command - toggle confirmation mode."""
    session.confirmation_enabled = not session.confirmation_enabled

    if session.confirmation_enabled:
        session.disabled_confirmations.clear()

    status = "disabled (YOLO mode)" if not session.confirmation_enabled else "enabled"
    ui.info(f"Tool confirmations {status}")
