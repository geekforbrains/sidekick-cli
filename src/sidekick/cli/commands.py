"""Command system for Sidekick CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .. import config, utils
from ..core.state import StateManager
from ..services.undo_service import perform_undo
from ..ui import console as ui


@dataclass
class CommandContext:
    """Context provided to commands during execution."""

    state_manager: StateManager


class Command(ABC):
    """Base class for all commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The primary name of the command."""
        pass

    @property
    @abstractmethod
    def aliases(self) -> List[str]:
        """Alternative names/aliases for the command."""
        pass

    @property
    def description(self) -> str:
        """Description of what the command does."""
        return ""

    @abstractmethod
    async def execute(self, args: List[str], context: CommandContext) -> Any:
        """
        Execute the command.

        Args:
            args: Command arguments (excluding the command name)
            context: Execution context with state and config

        Returns:
            Command-specific return value
        """
        pass


class YoloCommand(Command):
    """Toggle YOLO mode (skip confirmations)."""

    @property
    def name(self) -> str:
        return "yolo"

    @property
    def aliases(self) -> List[str]:
        return ["/yolo"]

    @property
    def description(self) -> str:
        return "Toggle YOLO mode (skip tool confirmations)"

    async def execute(self, args: List[str], context: CommandContext) -> None:
        state = context.state_manager.session
        state.yolo = not state.yolo
        if state.yolo:
            await ui.success("Ooh shit, its YOLO time!\n")
        else:
            await ui.info("Pfft, boring...\n")


class DumpCommand(Command):
    """Dump message history."""

    @property
    def name(self) -> str:
        return "dump"

    @property
    def aliases(self) -> List[str]:
        return ["/dump"]

    @property
    def description(self) -> str:
        return "Dump the current message history"

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.dump_messages(context.state_manager.session.messages)


class ClearCommand(Command):
    """Clear screen and message history."""

    @property
    def name(self) -> str:
        return "clear"

    @property
    def aliases(self) -> List[str]:
        return ["/clear"]

    @property
    def description(self) -> str:
        return "Clear the screen and message history"

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.clear()
        context.state_manager.session.messages = []


class HelpCommand(Command):
    """Show help information."""

    @property
    def name(self) -> str:
        return "help"

    @property
    def aliases(self) -> List[str]:
        return ["/help"]

    @property
    def description(self) -> str:
        return "Show help information"

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.help()


class UndoCommand(Command):
    """Undo the last file operation."""

    @property
    def name(self) -> str:
        return "undo"

    @property
    def aliases(self) -> List[str]:
        return ["/undo"]

    @property
    def description(self) -> str:
        return "Undo the last file operation"

    async def execute(self, args: List[str], context: CommandContext) -> None:
        success, message = perform_undo()
        if success:
            await ui.success(message)
        else:
            await ui.warning(message)


class CompactCommand(Command):
    """Compact conversation context."""

    @property
    def name(self) -> str:
        return "compact"

    @property
    def aliases(self) -> List[str]:
        return ["/compact"]

    @property
    def description(self) -> str:
        return "Summarize and compact the conversation history"

    async def execute(self, args: List[str], context: CommandContext) -> None:
        # Import here to avoid circular dependency
        from .repl import process_request

        # Get the current agent, create a summary of context, and trim message history
        await process_request(
            "Summarize the conversation so far", context.state_manager, output=False
        )
        await ui.success("Context history has been summarized and truncated.")
        context.state_manager.session.messages = context.state_manager.session.messages[-2:]


class ModelCommand(Command):
    """Manage model selection."""

    @property
    def name(self) -> str:
        return "model"

    @property
    def aliases(self) -> List[str]:
        return ["/model"]

    @property
    def description(self) -> str:
        return "List models or select a model (e.g., /model 3 or /model 3 default)"

    async def execute(self, args: List[str], context: CommandContext) -> Optional[str]:
        if not args:
            # No arguments - list models
            await ui.models()
            return None

        # Parse model index
        try:
            model_index = int(args[0])
        except ValueError:
            await ui.error(f"Invalid model index: {args[0]}")
            return None

        # Get model list
        models = list(config.MODELS.keys())
        if model_index < 0 or model_index >= len(models):
            await ui.error(f"Model index {model_index} out of range")
            return None

        # Set the model
        model = models[model_index]
        context.state_manager.session.current_model = model

        # Check if setting as default
        if len(args) > 1 and args[1] == "default":
            utils.user_config.set_default_model(model)
            await ui.muted("Updating default model")
            return "restart"
        else:
            # Show success message with the new model
            await ui.success(f"Switched to model: {model}")
            return None


class CommandRegistry:
    """Registry for managing commands."""

    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._process_request_callback: Optional[Callable] = None

    def register(self, command: Command) -> None:
        """Register a command and its aliases."""
        # Register by primary name
        self._commands[command.name] = command

        # Register all aliases
        for alias in command.aliases:
            self._commands[alias.lower()] = command

    def register_all_default_commands(self) -> None:
        """Register all default commands."""
        self.register(YoloCommand())
        self.register(DumpCommand())
        self.register(ClearCommand())
        self.register(HelpCommand())
        self.register(UndoCommand())
        self.register(CompactCommand())
        self.register(ModelCommand())

    def set_process_request_callback(self, callback: Callable) -> None:
        """Set the process_request callback for commands that need it."""
        self._process_request_callback = callback

    async def execute(self, command_text: str, context: CommandContext) -> Any:
        """
        Execute a command.

        Args:
            command_text: The full command text
            context: Execution context

        Returns:
            Command-specific return value, or None if command not found

        Raises:
            ValueError: If command is not found
        """
        parts = command_text.split()
        if not parts:
            raise ValueError("Empty command")

        command_name = parts[0].lower()
        args = parts[1:]

        if command_name not in self._commands:
            raise ValueError(f"Unknown command: {command_name}")

        command = self._commands[command_name]

        # Special handling for CompactCommand to inject process_request
        if isinstance(command, CompactCommand) and self._process_request_callback:
            # Temporarily inject the callback
            import sys

            module = sys.modules[command.__module__]
            original_process_request = getattr(module, "process_request", None)
            setattr(module, "process_request", self._process_request_callback)
            try:
                return await command.execute(args, context)
            finally:
                if original_process_request is None:
                    delattr(module, "process_request")
                else:
                    setattr(module, "process_request", original_process_request)

        return await command.execute(args, context)

    def is_command(self, text: str) -> bool:
        """Check if text starts with a registered command."""
        if not text:
            return False

        parts = text.split()
        if not parts:
            return False

        return parts[0].lower() in self._commands

    def get_command_names(self) -> List[str]:
        """Get all registered command names (including aliases)."""
        return sorted(self._commands.keys())
