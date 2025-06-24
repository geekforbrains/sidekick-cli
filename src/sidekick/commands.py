"""Command handlers for Sidekick CLI slash commands."""

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
    status = "disabled (YOLO mode)" if not session.confirmation_enabled else "enabled"
    ui.info(f"Tool confirmations {status}")


async def handle_model(args: list[str]):
    """Handle /model command - list, switch, or set default model."""
    if len(args) == 0:
        # List available models
        ui.info("Available models:")
        for i, model_name in enumerate(MODELS.keys(), 1):
            current = " (current)" if model_name == session.current_model else ""
            ui.bullet(f"{i}. {model_name}{current}")
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
    ui.info("Session Usage Statistics")

    # Show total tokens and cost
    if session.total_tokens > 0:
        ui.bullet(f"Total tokens: {session.total_tokens:,}")
        ui.bullet(f"Total cost: ${session.total_cost:.5f}")

    # Show last request details if available
    if session.last_usage:
        ui.line()
        ui.info("Last request:")
        ui.bullet(f"Input tokens: {session.last_usage['input_tokens']:,}")
        ui.bullet(f"Cached tokens: {session.last_usage['cached_tokens']:,}")
        ui.bullet(f"Output tokens: {session.last_usage['output_tokens']:,}")
        ui.bullet(f"Request cost: ${session.last_usage['request_cost']:.5f}")

    # Show tool usage breakdown
    if session.tool_usage:
        ui.line()
        ui.info("Tools used this session:")
        for tool_name, count in sorted(session.tool_usage.items()):
            display_name = ui.format_tool_name(tool_name)
            ui.bullet(f"{display_name}: {count}x")

    if not session.total_tokens and not session.tool_usage:
        ui.muted("No usage data yet in this session")


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
    }

    handler = handlers.get(command)
    if handler:
        await handler()
        return True

    return False
