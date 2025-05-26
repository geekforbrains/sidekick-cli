"""Panel display functions for Sidekick UI."""

from typing import Any, Optional, Union

from rich.markdown import Markdown
from rich.pretty import Pretty
from rich.table import Table

from sidekick.configuration import ModelRegistry
from sidekick.constants import (APP_NAME, CMD_CLEAR, CMD_COMPACT, CMD_DUMP, CMD_EXIT, CMD_HELP,
                                CMD_MODEL, CMD_UNDO, CMD_YOLO, DESC_CLEAR, DESC_COMPACT, DESC_DUMP,
                                DESC_EXIT, DESC_HELP, DESC_MODEL, DESC_MODEL_DEFAULT,
                                DESC_MODEL_SWITCH, DESC_UNDO, DESC_YOLO, PANEL_AVAILABLE_COMMANDS,
                                PANEL_ERROR, PANEL_MESSAGE_HISTORY, PANEL_MODELS)
from sidekick.types import SessionState
from sidekick.ui.decorators import create_sync_wrapper
from sidekick.ui.output import print
from sidekick.ui.shared import create_padded_panel, theme


@create_sync_wrapper
async def panel(
    title: str,
    text: Union[str, Markdown, Pretty],
    border_style: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Display a rich panel."""
    border_style = border_style or kwargs.get("style")
    panel_obj = create_padded_panel(title, text, border_style=border_style)
    await print(panel_obj, **kwargs)


async def agent(text: str, bottom: int = 1) -> None:
    """Display an agent panel."""
    panel_obj = create_padded_panel(
        APP_NAME, Markdown(text), border_style=theme.primary, padding_bottom=bottom
    )
    await print(panel_obj)


async def error(text: str) -> None:
    """Display an error panel."""
    panel_obj = create_padded_panel(PANEL_ERROR, text, border_style=theme.error)
    await print(panel_obj)


async def dump_messages(messages_list=None, session: SessionState = None) -> None:
    """Display message history panel."""
    if messages_list is None and session:
        messages = Pretty(session.messages)
    elif messages_list is not None:
        messages = Pretty(messages_list)
    else:
        messages = Pretty([])
    panel_obj = create_padded_panel(PANEL_MESSAGE_HISTORY, messages, border_style=theme.muted)
    await print(panel_obj)


async def models(session: SessionState = None) -> None:
    """Display available models panel."""
    model_registry = ModelRegistry()
    model_ids = list(model_registry.list_models().keys())
    model_list = "\n".join([f"{index} - {model}" for index, model in enumerate(model_ids)])
    current_model = session.current_model if session else "unknown"
    text = f"Current model: {current_model}\n\n{model_list}"
    panel_obj = create_padded_panel(PANEL_MODELS, text, border_style=theme.muted)
    await print(panel_obj)


async def help(command_registry=None) -> None:
    """Display the available commands organized by category."""
    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    table.add_column("Command", style="white", justify="right")
    table.add_column("Description", style="white")

    if command_registry:
        # Use the new command registry to display commands by category
        from ..cli.commands import CommandCategory

        category_order = [
            CommandCategory.SYSTEM,
            CommandCategory.NAVIGATION,
            CommandCategory.DEVELOPMENT,
            CommandCategory.MODEL,
            CommandCategory.DEBUG,
        ]

        for category in category_order:
            commands = command_registry.get_commands_by_category(category)
            if commands:
                # Add category header
                table.add_row("", "")
                table.add_row(f"[bold]{category.value.title()}[/bold]", "")

                # Add commands in this category
                for command in commands:
                    # Show primary command name
                    cmd_display = f"/{command.name}"
                    table.add_row(cmd_display, command.description)

                    # Special handling for model command variations
                    if command.name == "model":
                        table.add_row(f"{cmd_display} <n>", DESC_MODEL_SWITCH)
                        table.add_row(f"{cmd_display} <n> default", DESC_MODEL_DEFAULT)

        # Add built-in commands
        table.add_row("", "")
        table.add_row("[bold]Built-in[/bold]", "")
        table.add_row(CMD_EXIT, DESC_EXIT)
    else:
        # Fallback to static command list
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

    panel_obj = create_padded_panel(PANEL_AVAILABLE_COMMANDS, table, border_style=theme.muted)
    await print(panel_obj)


@create_sync_wrapper
async def tool_confirm(
    title: str, content: Union[str, Markdown], filepath: Optional[str] = None
) -> None:
    """Display a tool confirmation panel."""
    bottom_padding = 0 if filepath else 1
    panel_obj = create_padded_panel(
        title, content, border_style=theme.warning, padding_bottom=bottom_padding
    )
    await print(panel_obj)


# Auto-generated sync versions
sync_panel = panel.sync  # type: ignore
sync_tool_confirm = tool_confirm.sync  # type: ignore
