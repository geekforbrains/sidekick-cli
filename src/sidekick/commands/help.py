"""Handle /help command."""

from sidekick import ui


async def handle_help():
    """Handle /help command - show available commands."""
    ui.line()
    ui.help()
