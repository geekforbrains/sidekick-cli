"""Handle /clear command."""

from sidekick import ui
from sidekick.session import session


async def handle_clear():
    """Handle /clear command - clear conversation history and screen."""
    session.messages.clear()
    ui.banner()
    ui.success("Conversation history cleared")
