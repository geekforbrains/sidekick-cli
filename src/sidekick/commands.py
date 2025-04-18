from sidekick import session, ui
from sidekick.utils.undo import perform_undo


def handle_command(command: str) -> bool:
    """
    Handles a command string.

    Args:
        command: The command string entered by the user.

    Returns:
        True if the command was handled, False otherwise.
    """
    ui.warning(f"Command: {command}")
    # cmd_lower = command.lower()
    # parts = cmd_lower.split()
    # base_command = parts[0]
    #
    # if base_command in self.commands:
    #     await self.commands[base_command](command)
    #     return True
    # return False


def _toggle_yolo(self, command: str):
    session.yolo = not session.yolo
    if session.yolo:
        ui.success("Ooh shit, its YOLO time!\n")
    else:
        ui.status("Pfft, boring...\n")


def _dump_messages(self, command: str):
    ui.dump_messages()


def _clear_screen(self, command: str):
    ui.console.clear()
    ui.show_banner()
    session.messages = []


def _show_help(self, command: str):
    ui.show_help()


def _perform_undo(self, command: str):
    success, message = perform_undo()
    if success:
        ui.success(message)
    else:
        ui.warning(message)


def _compact_context(self, command: str):
    raise Exception("not implemented")


def _handle_model_command(self, command: str):
    parts = command.split()
    if len(parts) > 1:
        model = parts[1]
        self.agent.switch_model(model)
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
