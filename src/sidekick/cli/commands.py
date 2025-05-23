"""Command system for Sidekick CLI."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from .. import utils
from ..configuration.models import ModelRegistry
from ..exceptions import ValidationError
from ..services.undo_service import perform_undo
from ..types import CommandArgs, CommandContext, CommandResult, ProcessRequestCallback
from ..ui import console as ui


class CommandCategory(Enum):
    """Categories for organizing commands."""

    SYSTEM = "system"
    NAVIGATION = "navigation"
    DEVELOPMENT = "development"
    MODEL = "model"
    DEBUG = "debug"


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

    @property
    def category(self) -> CommandCategory:
        """Category this command belongs to."""
        return CommandCategory.SYSTEM

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
    category: CommandCategory = CommandCategory.SYSTEM


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

    @property
    def category(self) -> CommandCategory:
        """Category this command belongs to."""
        return self.spec.category


class YoloCommand(SimpleCommand):
    """Toggle YOLO mode (skip confirmations)."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="yolo",
                aliases=["/yolo"],
                description="Toggle YOLO mode (skip tool confirmations)",
                category=CommandCategory.DEVELOPMENT,
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
                name="dump",
                aliases=["/dump"],
                description="Dump the current message history",
                category=CommandCategory.DEBUG,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.dump_messages(context.state_manager.session.messages)


class ClearCommand(SimpleCommand):
    """Clear screen and message history."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="clear",
                aliases=["/clear"],
                description="Clear the screen and message history",
                category=CommandCategory.NAVIGATION,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.clear()
        context.state_manager.session.messages = []


class HelpCommand(SimpleCommand):
    """Show help information."""

    def __init__(self, command_registry=None):
        super().__init__(
            CommandSpec(
                name="help",
                aliases=["/help"],
                description="Show help information",
                category=CommandCategory.SYSTEM,
            )
        )
        self._command_registry = command_registry

    async def execute(self, args: List[str], context: CommandContext) -> None:
        await ui.help(self._command_registry)


class UndoCommand(SimpleCommand):
    """Undo the last file operation."""

    def __init__(self):
        super().__init__(
            CommandSpec(
                name="undo",
                aliases=["/undo"],
                description="Undo the last file operation",
                category=CommandCategory.DEVELOPMENT,
            )
        )

    async def execute(self, args: List[str], context: CommandContext) -> None:
        success, message = perform_undo(context.state_manager)
        if success:
            await ui.success(message)
        else:
            await ui.warning(message)


class CompactCommand(SimpleCommand):
    """Compact conversation context."""

    def __init__(self, process_request_callback: Optional[ProcessRequestCallback] = None):
        super().__init__(
            CommandSpec(
                name="compact",
                aliases=["/compact"],
                description="Summarize and compact the conversation history",
                category=CommandCategory.SYSTEM,
            )
        )
        self._process_request = process_request_callback

    async def execute(self, args: List[str], context: CommandContext) -> None:
        # Use the injected callback or get it from context
        process_request = self._process_request or context.process_request

        if not process_request:
            await ui.error("Compact command not available - process_request not configured")
            return

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
                category=CommandCategory.MODEL,
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


@dataclass
class CommandDependencies:
    """Container for command dependencies."""

    process_request_callback: Optional[ProcessRequestCallback] = None
    command_registry: Optional[Any] = None  # Reference to the registry itself


class CommandFactory:
    """Factory for creating commands with proper dependency injection."""

    def __init__(self, dependencies: Optional[CommandDependencies] = None):
        self.dependencies = dependencies or CommandDependencies()

    def create_command(self, command_class: Type[Command]) -> Command:
        """Create a command instance with proper dependencies."""
        # Special handling for commands that need dependencies
        if command_class == CompactCommand:
            return CompactCommand(self.dependencies.process_request_callback)
        elif command_class == HelpCommand:
            return HelpCommand(self.dependencies.command_registry)

        # Default creation for commands without dependencies
        return command_class()

    def update_dependencies(self, **kwargs) -> None:
        """Update factory dependencies."""
        for key, value in kwargs.items():
            if hasattr(self.dependencies, key):
                setattr(self.dependencies, key, value)


class CommandRegistry:
    """Registry for managing commands with auto-discovery and categories."""

    def __init__(self, factory: Optional[CommandFactory] = None):
        self._commands: Dict[str, Command] = {}
        self._categories: Dict[CommandCategory, List[Command]] = {
            category: [] for category in CommandCategory
        }
        self._factory = factory or CommandFactory()
        self._discovered = False

        # Set registry reference in factory dependencies
        self._factory.update_dependencies(command_registry=self)

    def register(self, command: Command) -> None:
        """Register a command and its aliases."""
        # Register by primary name
        self._commands[command.name] = command

        # Register all aliases
        for alias in command.aliases:
            self._commands[alias.lower()] = command

        # Add to category
        if command not in self._categories[command.category]:
            self._categories[command.category].append(command)

    def register_command_class(self, command_class: Type[Command]) -> None:
        """Register a command class using the factory."""
        command = self._factory.create_command(command_class)
        self.register(command)

    def discover_commands(self) -> None:
        """Auto-discover and register all command classes."""
        if self._discovered:
            return

        # List of all command classes to register
        command_classes = [
            YoloCommand,
            DumpCommand,
            ClearCommand,
            HelpCommand,
            UndoCommand,
            CompactCommand,
            ModelCommand,
        ]

        # Register all discovered commands
        for command_class in command_classes:
            self.register_command_class(command_class)

        self._discovered = True

    def register_all_default_commands(self) -> None:
        """Register all default commands (backward compatibility)."""
        self.discover_commands()

    def set_process_request_callback(self, callback: ProcessRequestCallback) -> None:
        """Set the process_request callback for commands that need it."""
        self._factory.update_dependencies(process_request_callback=callback)

        # Re-register CompactCommand with new dependency if already registered
        if "compact" in self._commands:
            self.register_command_class(CompactCommand)

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
        # Ensure commands are discovered
        self.discover_commands()

        parts = command_text.split()
        if not parts:
            raise ValidationError("Empty command")

        command_name = parts[0].lower()
        args = parts[1:]

        if command_name not in self._commands:
            raise ValidationError(f"Unknown command: {command_name}")

        command = self._commands[command_name]
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
        self.discover_commands()
        return sorted(self._commands.keys())

    def get_commands_by_category(self, category: CommandCategory) -> List[Command]:
        """Get all commands in a specific category."""
        self.discover_commands()
        return self._categories.get(category, [])

    def get_all_categories(self) -> Dict[CommandCategory, List[Command]]:
        """Get all commands organized by category."""
        self.discover_commands()
        return self._categories.copy()
