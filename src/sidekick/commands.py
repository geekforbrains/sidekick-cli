"""Command handlers for Sidekick CLI slash commands."""

from rich.table import Table

from sidekick import ui
from sidekick.config import update_config_file
from sidekick.constants import MODELS
from sidekick.session import session


async def handle_dump():
    """Handle /dump command - show message history."""
    ui.dump(session.messages)


async def handle_yolo():
    """Handle /yolo command - toggle confirmation mode."""
    session.confirmation_enabled = not session.confirmation_enabled

    # Clear disabled confirmations when toggling
    if session.confirmation_enabled:
        session.disabled_confirmations.clear()

    status = "disabled (YOLO mode)" if not session.confirmation_enabled else "enabled"
    ui.info(f"Tool confirmations {status}")


async def handle_model(args: list[str]):
    """Handle /model command - list, switch, or set default model."""
    if len(args) == 0:
        # List available models in a styled panel
        table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
        table.add_column("#", justify="right", style=ui.colors.primary)
        table.add_column("Model", style="white")

        for i, model_name in enumerate(MODELS.keys(), 1):
            label = model_name
            if model_name == session.current_model:
                label += " [dim](current)[/dim]"
            table.add_row(str(i), label)

        panel = ui.create_panel(table, "Available Models", ui.colors.muted)
        ui.display_panel(panel)

    elif len(args) >= 1:
        try:
            model_num = int(args[0])
            model_list = list(MODELS.keys())
            if 1 <= model_num <= len(model_list):
                selected_model = model_list[model_num - 1]

                if len(args) >= 2 and args[1] == "default":
                    # Set as default model in config
                    try:
                        update_config_file({"default_model": selected_model})
                        ui.success(f"Set {selected_model} as default model")
                    except Exception as e:
                        ui.error(f"Failed to update config: {e}")
                else:
                    # Switch to model for current session
                    session.current_model = selected_model
                    # Clear the agent cache and set flag for REPL to recreate agent
                    session.agents.clear()
                    session.model_switched = True
                    ui.info(f"Switched to model: {selected_model}")
            else:
                ui.error(f"Invalid model number. Choose between 1 and {len(model_list)}")
        except ValueError:
            ui.error("Invalid model number")


async def handle_usage():
    """Handle /usage command - show session usage statistics."""
    from rich.text import Text

    content = Text()

    # Show total tokens and cost
    if session.total_tokens > 0:
        content.append("Total Statistics\n", style=f"bold {ui.colors.primary}")
        content.append(f"  • Total tokens: {session.total_tokens:,}\n", style="white")
        content.append(f"  • Total cost: ${session.total_cost:.5f}\n", style="white")

    # Show last request details if available
    if session.last_usage:
        if session.total_tokens > 0:
            content.append("\n")
        content.append("Last Request\n", style=f"bold {ui.colors.primary}")
        content.append(f"  • Input tokens: {session.last_usage['input_tokens']:,}\n", style="white")
        content.append(
            f"  • Cached tokens: {session.last_usage['cached_tokens']:,}\n", style="white"
        )
        content.append(
            f"  • Output tokens: {session.last_usage['output_tokens']:,}\n", style="white"
        )
        content.append(
            f"  • Request cost: ${session.last_usage['request_cost']:.5f}\n", style="white"
        )

    if not session.total_tokens:
        content.append("No usage data yet in this session", style=ui.colors.muted)

    # Remove trailing newline if present
    if content.plain.endswith("\n"):
        content = Text(content.plain.rstrip("\n"))

    panel = ui.create_panel(content, "Session Usage Statistics", ui.colors.muted)
    ui.display_panel(panel)


async def handle_clear():
    """Handle /clear command - clear conversation history and screen."""
    # Clear the conversation history
    session.messages.clear()

    # Clear the screen and redisplay the banner
    ui.banner()

    # Show success message
    ui.success("Conversation history cleared")


async def handle_help():
    """Handle /help command - show available commands."""
    ui.help()


async def handle_command(user_input: str) -> bool:
    """Handle slash commands. Returns True if command was handled."""
    if not user_input.startswith("/"):
        return False

    parts = user_input.split()
    command = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    handlers = {
        "/dump": handle_dump,
        "/yolo": handle_yolo,
        "/model": lambda: handle_model(args),
        "/usage": handle_usage,
        "/clear": handle_clear,
        "/help": handle_help,
    }

    handler = handlers.get(command)
    if handler:
        await handler()
        return True

    return False
