from sidekick import session
from sidekick.agents.main import MainAgent
from sidekick.utils import ui
from sidekick.utils.undo import perform_undo


class CommandHandler:
    def __init__(self, agent: MainAgent, process_request_func: callable):
        self._process_request = process_request_func
        self.agent = agent
        self.commands = {
            "/yolo": self._toggle_yolo,
            "/dump": self._dump_messages,
            "/clear": self._clear_screen,
            "/help": self._show_help,
            "/undo": self._perform_undo,
            "/compact": self._compact_context,
            "/model": self._handle_model_command,
        }

    async def handle(self, command: str) -> bool:
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

        if base_command in self.commands:
            await self.commands[base_command](command)
            return True
        return False

    async def _toggle_yolo(self, command: str):
        session.yolo = not session.yolo
        if session.yolo:
            ui.success("Ooh shit, its YOLO time!\n")
        else:
            ui.status("Pfft, boring...\n")

    async def _dump_messages(self, command: str):
        ui.dump_messages()

    async def _clear_screen(self, command: str):
        ui.console.clear()
        ui.show_banner()
        session.messages = []

    async def _show_help(self, command: str):
        ui.show_help()

    async def _perform_undo(self, command: str):
        success, message = perform_undo()
        if success:
            ui.success(message)
        else:
            ui.warning(message)

    async def _compact_context(self, command: str):
        # This needs access to the process_request function,
        # which is currently in main.py. We might need to pass it in
        # or refactor process_request as well.
        # For now, we'll reference the agent directly, assuming process_request
        # might move or be accessible via the agent.
        # Ideally, process_request itself might be refactored later.
        from sidekick.main import process_request  # Temporary import

        await process_request(
            (
                "Summarize the context of this conversation into a concise "
                "breakdown, ensuring it contain's enough key details for "
                "future conversations."
            ),
            compact=True,
        )

    async def _handle_model_command(self, command: str):
        parts = command.split()
        if len(parts) > 1:
            model = parts[1]
            self.agent.switch_model(model)
        else:
            ui.show_models()
