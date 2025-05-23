"""Command system for Sidekick CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .. import utils
from ..configuration.models import ModelRegistry
from ..exceptions import ValidationError
from ..services.undo_service import perform_undo
from ..types import CommandArgs, CommandContext, CommandResult, ProcessRequestCallback
from ..ui import console as ui


class Command(ABC):
    """Base class for all commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The primary name of the command."""
        pass

    @property
    @abstractmethod
    def aliases(self) -> CommandArgs:
        """Alternative names/aliases for the command."""
        pass

    @property
    def description(self) -> str:
        """Description of what the command does."""
        return ""

    @abstractmethod
    async def execute(self, args: CommandArgs, context: CommandContext) -> CommandResult:
        """
        Execute the command.

        Args:
            args: Command arguments (excluding the command name)
            context: Execution context with state and config

        Returns:
            Command-specific return value
        """
        pass


@dataclass
class CommandSpec:
    """Specification for a command's metadata."""

    name: str
    aliases: List[str]
    description: str


class SimpleCommand(Command):
    """Base class for simple commands without complex logic."""

    def __init__(self, spec: CommandSpec):
        self.spec = spec

    @property
    def name(self) -> str:
        """The primary name of the command."""
        return self.spec.name

    @property
    def aliases(self) -> CommandArgs:
        """Alternative names/aliases for the command."""
        return self.spec.aliases

    @property
    def description(self) -> str:
        """Description of what the command does."""
        return self.spec.description


class YoloCommand(SimpleCommand):
    """Toggle YOLO mode (skip confirmations)."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="yolo",
                aliases=["/yolo"],
                description="Toggle YOLO mode (skip tool confirmations)",
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        state = context.state_manager.session
        state.yolo = not state.yolo
        if state.yolo:
            await ui.success("Ooh shit, its YOLO time!\n")
        else:
            await ui.info("Pfft, boring...\n")


class DumpCommand(SimpleCommand):
    """Dump message history."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="dump", aliases=["/dump"], description="Dump the current message history"
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.dump_messages(context.state_manager.session.messages)


class ClearCommand(SimpleCommand):
    """Clear screen and message history."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="clear", aliases=["/clear"], description="Clear the screen and message history"
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.clear()
        context.state_manager.session.messages = []


class HelpCommand(SimpleCommand):
    """Show help information."""

    def __init__(self):
        super().__init__(
            CommandSpec(name="help", aliases=["/help"], description="Show help information")
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.help()


class UndoCommand(SimpleCommand):
    """Undo the last file operation."""

    def __init__(self):
        super().__init__(
            CommandSpec(name="undo", aliases=["/undo"], description="Undo the last file operation")
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        success, message = perform_undo(context.state_manager)
        if success:
            await ui.success(message)
        else:
            await ui.warning(message)


class CompactCommand(SimpleCommand):
    """Compact conversation context."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="compact",
                aliases=["/compact"],
                description="Summarize and compact the conversation history",
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        # Import here to avoid circular dependency
        from .repl import process_request

        # Get the current agent, create a summary of context, and trim message history
        await process_request(
            "Summarize the conversation so far", context.state_manager, output=False
        )
        await ui.success("Context history has been summarized and truncated.")
        context.state_manager.session.messages = context.state_manager.session.messages[-2:]


class ModelCommand(SimpleCommand):
    """Manage model selection."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="model",
                aliases=["/model"],
                description="List models or select a model (e.g., /model 3 or /model 3 default)",
            )
        )

    async def execute(self, args: CommandArgs, context: CommandContext) -> Optional[str]:
        if not args:
            # No arguments - list models
            await ui.models(context.state_manager)
            return None

        # Parse model index
        try:
            model_index = int(args[0])
        except ValueError:
            await ui.error(f"Invalid model index: {args[0]}")
            return None

        # Get model list
        model_registry = ModelRegistry()
        models = list(model_registry.list_models().keys())
        if model_index < 0 or model_index >= len(models):
            await ui.error(f"Model index {model_index} out of range")
            return None

        # Set the model
        model = models[model_index]
        context.state_manager.session.current_model = model

        # Check if setting as default
        if len(args) > 1 and args[1] == "default":
            utils.user_config.set_default_model(model, context.state_manager)
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
        self._process_request_callback: Optional[ProcessRequestCallback] = None

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

    def set_process_request_callback(self, callback: ProcessRequestCallback) -> None:
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
            ValidationError: If command is not found or empty
        """
        parts = command_text.split()
        if not parts:
            raise ValidationError("Empty command")

        command_name = parts[0].lower()
        args = parts[1:]

        if command_name not in self._commands:
            raise ValidationError(f"Unknown command: {command_name}")

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

    def get_command_names(self) -> CommandArgs:
        """Get all registered command names (including aliases)."""
        return sorted(self._commands.keys())
