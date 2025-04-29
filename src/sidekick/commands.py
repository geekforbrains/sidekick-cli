from sidekick import session, ui, config
from sidekick.utils.undo import perform_undo
from sidekick.utils import user_config


def handle_command(command: str) -> bool:
    """
    Handles a command string.

    Args:
        command: The command string entered by the user.

    Returns:
        True if the command was handled, False otherwise.
    """
    cmd_lower = command.lower()
    parts = cmd_lower.split()
    base_command = parts[0]

    if base_command in COMMANDS:
        COMMANDS[base_command](*parts[1:])


def _toggle_yolo():
    session.yolo = not session.yolo
    if session.yolo:
        ui.success("Ooh shit, its YOLO time!\n")
    else:
        ui.status("Pfft, boring...\n")


def _dump_messages():
    ui.dump_messages()


def _clear_screen():
    ui.console.clear()
    ui.show_banner()
    session.messages = []


def _show_help():
    ui.show_help()


def _perform_undo():
    success, message = perform_undo()
    if success:
        ui.success(message)
    else:
        ui.warning(message)


def _compact_context():
    raise Exception("not implemented")


def _handle_model_command(model_index: int = None, action: str = None):
    if model_index:
        models = list(config.MODELS.keys())
        model = models[int(model_index)]
        session.current_model = model
        ui.success(f"Model changed to [bold]{model}[/bold]")
        if action == 'default':
            user_config.set_default_model(model)
            ui.muted("Model is now default")
    else:
        ui.show_models()


COMMANDS = {
    "/yolo": _toggle_yolo,
    "/dump": _dump_messages,
    "/clear": _clear_screen,
    "/help": _show_help,
    "/undo": _perform_undo,
    "/compact": _compact_context,
    "/model": _handle_model_command,
}
