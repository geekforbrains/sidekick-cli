"""Command system for Sidekick CLI."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from sidekick.configuration import ModelRegistry, set_default_model
from sidekick.exceptions import ValidationError
from sidekick.services.undo_service import get_undo_status, perform_undo
from sidekick.types import CommandArgs, CommandContext, CommandResult, ProcessRequestCallback
from sidekick.ui.output import clear, info, muted, success, warning
from sidekick.ui.panels import dump_messages, error, help
from sidekick.ui.panels import models as models_panel


class CommandCategory(Enum):
    """Categories for organizing commands."""

    SYSTEM = "system"
    NAVIGATION = "navigation"
    DEVELOPMENT = "development"
    MODEL = "model"
    DEBUG = "debug"


class Command(ABC):
    """Base class for all commands."""

    def __init__(
        self,
        name: str,
        aliases: List[str],
        description: str = "",
        category: CommandCategory = CommandCategory.SYSTEM,
    ):
        self._name = name
        self._aliases = aliases
        self._description = description
        self._category = category

    @property
    def name(self) -> str:
        """The primary name of the command."""
        return self._name

    @property
    def aliases(self) -> CommandArgs:
        """Alternative names/aliases for the command."""
        return self._aliases

    @property
    def description(self) -> str:
        """Description of what the command does."""
        return self._description

    @property
    def category(self) -> CommandCategory:
        """Category this command belongs to."""
        return self._category

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


class YoloCommand(Command):
    """Toggle YOLO mode (skip confirmations)."""

    def __init__(self):
        super().__init__(
            name="yolo",
            aliases=["/yolo"],
            description="Toggle YOLO mode (skip tool confirmations)",
            category=CommandCategory.DEVELOPMENT,
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        state = context.session
        state.yolo = not state.yolo
        if state.yolo:
            await success("Ooh shit, its YOLO time!\n")
        else:
            await info("Pfft, boring...\n")


class DumpCommand(Command):
    """Dump message history."""

    def __init__(self):
        super().__init__(
            name="dump",
            aliases=["/dump"],
            description="Dump the current message history",
            category=CommandCategory.DEBUG,
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await dump_messages(context.session.messages)


class ClearCommand(Command):
    """Clear screen and message history."""

    def __init__(self):
        super().__init__(
            name="clear",
            aliases=["/clear"],
            description="Clear the screen and message history",
            category=CommandCategory.NAVIGATION,
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await clear()
        context.session.messages = []


class HelpCommand(Command):
    """Show help information."""

    def __init__(self, command_registry=None):
        super().__init__(
            name="help",
            aliases=["/help"],
            description="Show help information",
            category=CommandCategory.SYSTEM,
        )
        self._command_registry = command_registry

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await help(self._command_registry)

        if context.session:
            available, status = get_undo_status(context.session)
            await muted(f"Undo: {status}")


class UndoCommand(Command):
    """Undo the last file operation."""

    def __init__(self):
        super().__init__(
            name="undo",
            aliases=["/undo"],
            description="Undo the last file operation",
            category=CommandCategory.DEVELOPMENT,
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        success, message = perform_undo(context.session)
        if success:
            await success(message)
        else:
            if "not initialized" in message.lower():
                await warning("Undo system not available")
                await muted("Ensure you're in a Git project and not in home directory")
            elif "nothing to undo" in message.lower():
                await info("No changes to undo - no commits found")
            else:
                await warning(message)


class CompactCommand(Command):
    """Compact conversation context."""

    def __init__(self, process_request_callback: Optional[ProcessRequestCallback] = None):
        super().__init__(
            name="compact",
            aliases=["/compact"],
            description="Summarize and compact the conversation history",
            category=CommandCategory.SYSTEM,
        )
        self._process_request = process_request_callback

    async def execute(self, args: List[str], context: CommandContext) -> None:
        # Use the injected callback or get it from context
        process_request = self._process_request or context.process_request

        if not process_request:
            await error("Compact command not available - process_request not configured")
            return

        # Get the current agent, create a summary of context, and trim message history
        await process_request("Summarize the conversation so far", context.session, output=False)
        await success("Context history has been summarized and truncated.")
        context.session.messages = context.session.messages[-2:]


class ModelCommand(Command):
    """Manage model selection."""

    def __init__(self):
        super().__init__(
            name="model",
            aliases=["/model"],
            description="List models or select a model (e.g., /model 3 or /model 3 default)",
            category=CommandCategory.MODEL,
        )

    async def execute(self, args: CommandArgs, context: CommandContext) -> Optional[str]:
        if not args:
            # No arguments - list models
            await models_panel(context.session)
            return None

        # Parse model index
        try:
            model_index = int(args[0])
        except ValueError:
            await error(f"Invalid model index: {args[0]}")
            return None

        # Get model list
        model_registry = ModelRegistry()
        models = list(model_registry.list_models().keys())
        if model_index < 0 or model_index >= len(models):
            await error(f"Model index {model_index} out of range")
            return None

        # Set the model
        model = models[model_index]
        context.session.current_model = model

        # Check if setting as default
        if len(args) > 1 and args[1] == "default":
            set_default_model(model, context.session)
            await muted("Updating default model")
        else:
            # Show success message with the new model
            await success(f"Switched to model: {model}")

        # Always restart to reload MCP servers when switching models
        return "restart"


class CommandRegistry:
    """Simple registry for managing commands."""

    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._categories: Dict[CommandCategory, List[Command]] = {
            category: [] for category in CommandCategory
        }
        self._process_request_callback: Optional[ProcessRequestCallback] = None
        self._register_default_commands()

    def _register_default_commands(self) -> None:
        """Register all default commands."""
        commands = [
            YoloCommand(),
            DumpCommand(),
            ClearCommand(),
            UndoCommand(),
            ModelCommand(),
        ]

        # Register help and compact commands with dependencies
        help_command = HelpCommand(self)
        commands.append(help_command)

        compact_command = CompactCommand(self._process_request_callback)
        commands.append(compact_command)

        for command in commands:
            self._register_command(command)

    def _register_command(self, command: Command) -> None:
        """Register a command and its aliases."""
        # Register by primary name
        self._commands[command.name] = command

        # Register all aliases
        for alias in command.aliases:
            self._commands[alias.lower()] = command

        # Add to category
        if command not in self._categories[command.category]:
            self._categories[command.category].append(command)

    def set_process_request_callback(self, callback: ProcessRequestCallback) -> None:
        """Set the process_request callback for commands that need it."""
        self._process_request_callback = callback

        # Re-register CompactCommand with new dependency
        compact_command = CompactCommand(callback)
        self._register_command(compact_command)

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
        return await command.execute(args, context)

    def get_command_names(self) -> CommandArgs:
        """Get all registered command names (including aliases)."""
        return sorted(self._commands.keys())

    def get_commands_by_category(self, category: CommandCategory) -> List[Command]:
        """Get all commands in a specific category."""
        return self._categories.get(category, [])

    def get_all_categories(self) -> Dict[CommandCategory, List[Command]]:
        """Get all commands organized by category."""
        return self._categories.copy()
