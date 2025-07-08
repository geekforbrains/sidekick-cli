"""Handle /clear command."""

from sidekick import ui


async def handle_clear(message_history):
    """Handle /clear command - clear conversation history and screen."""
    if message_history:
        message_history.clear()
        ui.banner()
        ui.success("Conversation history cleared")
    else:
        ui.error("Message history not available")
