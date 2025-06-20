"""Command handlers for Sidekick CLI slash commands."""

from sidekick import session, ui
from sidekick.config import MODELS, update_config_file


async def handle_dump():
    """Handle /dump command - show message history."""
    await ui.dump(session.messages)


async def handle_yolo():
    """Handle /yolo command - toggle confirmation mode."""
    session.confirmation_enabled = not session.confirmation_enabled
    status = "disabled (YOLO mode)" if not session.confirmation_enabled else "enabled"
    await ui.info(f"Tool confirmations {status}")


async def handle_model(args: list[str]):
    """Handle /model command - list, switch, or set default model."""
    if len(args) == 0:
        # List available models
        await ui.info("Available models:")
        for i, model_name in enumerate(MODELS.keys(), 1):
            current = " (current)" if model_name == session.current_model else ""
            await ui.bullet(f"{i}. {model_name}{current}")
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
                        await ui.success(f"Set {selected_model} as default model")
                    except Exception as e:
                        await ui.error(f"Failed to update config: {e}")
                else:
                    # Switch to model for current session
                    session.current_model = selected_model
                    # Clear the agent cache for the old model
                    session.agents.clear()
                    await ui.info(f"Switched to model: {selected_model}")
            else:
                await ui.error(f"Invalid model number. Choose between 1 and {len(model_list)}")
        except ValueError:
            await ui.error("Invalid model number")


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
    }

    handler = handlers.get(command)
    if handler:
        await handler()
        return True

    return False
