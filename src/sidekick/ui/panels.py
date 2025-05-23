"""Panel display functions for Sidekick UI."""

from typing import Any, Optional, Union

from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from sidekick.configuration.models import ModelRegistry
from sidekick.constants import (APP_NAME, CMD_CLEAR, CMD_COMPACT, CMD_DUMP, CMD_EXIT, CMD_HELP,
                                CMD_MODEL, CMD_UNDO, CMD_YOLO, DESC_CLEAR, DESC_COMPACT, DESC_DUMP,
                                DESC_EXIT, DESC_HELP, DESC_MODEL, DESC_MODEL_DEFAULT,
                                DESC_MODEL_SWITCH, DESC_UNDO, DESC_YOLO, PANEL_AVAILABLE_COMMANDS,
                                PANEL_ERROR, PANEL_MESSAGE_HISTORY, PANEL_MODELS, UI_COLORS)
from sidekick.core.state import StateManager
from sidekick.utils.file_utils import DotDict

from .output import print

colors = DotDict(UI_COLORS)


async def panel(
    title: str,
    text: Union[str, Markdown, Pretty],
    top: int = 1,
    right: int = 0,
    bottom: int = 1,
    left: int = 1,
    border_style: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Display a rich panel."""
    border_style = border_style or kwargs.get("style")
    panel_obj = Panel(Padding(text, 1), title=title, title_align="left", border_style=border_style)
    await print(Padding(panel_obj, (top, right, bottom, left)), **kwargs)


async def agent(text: str, bottom: int = 1) -> None:
    """Display an agent panel."""
    await panel(APP_NAME, Markdown(text), bottom=bottom, border_style=colors.primary)


async def error(text: str) -> None:
    """Display an error panel."""
    await panel(PANEL_ERROR, text, style=colors.error)


async def dump_messages(messages_list=None, state_manager: StateManager = None) -> None:
    """Display message history panel."""
    if messages_list is None and state_manager:
        # Get messages from state manager
        messages = Pretty(state_manager.session.messages)
    elif messages_list is not None:
        messages = Pretty(messages_list)
    else:
        # No messages available
        messages = Pretty([])
    await panel(PANEL_MESSAGE_HISTORY, messages, style=colors.muted)


async def models(state_manager: StateManager = None) -> None:
    """Display available models panel."""
    model_registry = ModelRegistry()
    model_ids = list(model_registry.list_models().keys())
    model_list = "\n".join([f"{index} - {model}" for index, model in enumerate(model_ids)])
    current_model = state_manager.session.current_model if state_manager else "unknown"
    text = f"Current model: {current_model}\n\n{model_list}"
    await panel(PANEL_MODELS, text, border_style=colors.muted)


async def help() -> None:
    """Display the available commands."""
    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    table.add_column("Command", style="white", justify="right")
    table.add_column("Description", style="white")

    commands = [
        (CMD_HELP, DESC_HELP),
        (CMD_CLEAR, DESC_CLEAR),
        (CMD_DUMP, DESC_DUMP),
        (CMD_YOLO, DESC_YOLO),
        (CMD_UNDO, DESC_UNDO),
        (CMD_COMPACT, DESC_COMPACT),
        (CMD_MODEL, DESC_MODEL),
        (f"{CMD_MODEL} <n>", DESC_MODEL_SWITCH),
        (f"{CMD_MODEL} <n> default", DESC_MODEL_DEFAULT),
        (CMD_EXIT, DESC_EXIT),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    await panel(PANEL_AVAILABLE_COMMANDS, table, border_style=colors.muted)


async def tool_confirm(
    title: str, content: Union[str, Markdown], filepath: Optional[str] = None
) -> None:
    """Display a tool confirmation panel."""
    bottom_padding = 0 if filepath else 1
    await panel(title, content, bottom=bottom_padding, border_style=colors.warning)


# Synchronous versions for use with run_in_terminal
def sync_panel(
    title: str,
    text: Union[str, Markdown, Pretty],
    top: int = 1,
    right: int = 0,
    bottom: int = 1,
    left: int = 1,
    border_style: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Synchronous version of panel display."""
    from rich.console import Console

    console = Console()
    border_style = border_style or kwargs.get("style")
    panel_obj = Panel(Padding(text, 1), title=title, title_align="left", border_style=border_style)
    console.print(Padding(panel_obj, (top, right, bottom, left)), **kwargs)


def sync_tool_confirm(
    title: str, content: Union[str, Markdown], filepath: Optional[str] = None
) -> None:
    """Synchronous version of tool confirmation panel."""
    bottom_padding = 0 if filepath else 1
    sync_panel(title, content, bottom=bottom_padding, border_style=colors.warning)
