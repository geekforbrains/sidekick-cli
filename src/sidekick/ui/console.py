"""Main console coordination module for Sidekick UI.

This module re-exports functions from specialized UI modules to maintain
backward compatibility while organizing code into focused modules.
"""

from rich.console import Console as RichConsole
from rich.markdown import Markdown

from .input import formatted_text, input, multiline_input
from .keybindings import create_key_bindings
from .output import (banner, clear, info, line, muted, print, spinner, success, sync_print,
                     sync_warning, update_available, usage, version, warning)
from .panels import (agent, dump_messages, error, help, models, panel, sync_panel,
                     sync_tool_confirm, tool_confirm)
from .prompt_manager import PromptConfig, PromptManager
from .validators import ModelValidator

console = RichConsole()
kb = create_key_bindings()


def markdown(text: str) -> Markdown:
    """Create a Markdown object."""
    return Markdown(text)


__all__ = [
    "formatted_text",
    "input",
    "multiline_input",
    "create_key_bindings",
    "kb",
    "banner",
    "clear",
    "console",
    "info",
    "line",
    "muted",
    "print",
    "spinner",
    "success",
    "sync_print",
    "sync_warning",
    "update_available",
    "usage",
    "version",
    "warning",
    "agent",
    "dump_messages",
    "error",
    "help",
    "models",
    "panel",
    "sync_panel",
    "sync_tool_confirm",
    "tool_confirm",
    "PromptConfig",
    "PromptManager",
    "ModelValidator",
    "markdown",
]
