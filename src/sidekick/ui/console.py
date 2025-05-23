from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.validation import ValidationError, Validator
from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from sidekick.configuration.models import ModelRegistry
from sidekick.configuration.settings import ApplicationSettings
from sidekick.constants import (APP_NAME, CMD_CLEAR, CMD_COMPACT, CMD_DUMP, CMD_EXIT, CMD_HELP,
                                CMD_MODEL, CMD_UNDO, CMD_YOLO, DESC_CLEAR, DESC_COMPACT, DESC_DUMP,
                                DESC_EXIT, DESC_HELP, DESC_MODEL, DESC_MODEL_DEFAULT,
                                DESC_MODEL_SWITCH, DESC_UNDO, DESC_YOLO, MSG_UPDATE_AVAILABLE,
                                MSG_UPDATE_INSTRUCTION, MSG_VERSION_DISPLAY,
                                PANEL_AVAILABLE_COMMANDS, PANEL_ERROR, PANEL_MESSAGE_HISTORY,
                                PANEL_MODELS, UI_COLORS, UI_PROMPT_PREFIX, UI_THINKING_MESSAGE)
from sidekick.core.state import StateManager
from sidekick.exceptions import SidekickAbort
from sidekick.utils.file_utils import DotDict

BANNER = """\
███████╗██╗██████╗ ███████╗██╗  ██╗██╗ ██████╗██╗  ██╗
██╔════╝██║██╔══██╗██╔════╝██║ ██╔╝██║██╔════╝██║ ██╔╝
███████╗██║██║  ██║█████╗  █████╔╝ ██║██║     █████╔╝
╚════██║██║██║  ██║██╔══╝  ██╔═██╗ ██║██║     ██╔═██╗
███████║██║██████╔╝███████╗██║  ██╗██║╚██████╗██║  ██╗
╚══════╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝"""


console = Console()
colors = DotDict(UI_COLORS)


# =============================================================================
# KEY BINDINGS
# =============================================================================


kb = KeyBindings()


@kb.add("escape", eager=True)
def _cancel(event):
    """Kill the running agent task, if any."""
    # Key bindings can't easily access state_manager, so we'll handle this differently
    # This will be handled in the REPL where state is available
    if (
        hasattr(event.app, "current_task")
        and event.app.current_task
        and not event.app.current_task.done()
    ):
        event.app.current_task.cancel()
        event.app.invalidate()


@kb.add("enter")
def _submit(event):
    """Submit the current buffer."""
    event.current_buffer.validate_and_handle()


@kb.add("c-o")  # ctrl+o
def _newline(event):
    """Insert a newline character."""
    event.current_buffer.insert_text("\n")


# =============================================================================
# CLASSES & UTILS
# =============================================================================


class ModelValidator(Validator):
    """Validate default provider selection"""

    def __init__(self, index):
        self.index = index

    def validate(self, document):
        text = document.text.strip()
        if not text:
            raise ValidationError(message="Provider number cannot be empty")
        elif text and not text.isdigit():
            raise ValidationError(message="Invalid provider number")
        elif text.isdigit():
            number = int(text)
            if number < 0 or number >= self.index:
                raise ValidationError(
                    message="Invalid provider number",
                )


async def line():
    await run_in_terminal(lambda: console.line())


def formatted_text(text: str):
    return HTML(text)


def markdown(text: str):
    return Markdown(text)


async def spinner(show=True, spinner_obj=None, state_manager: StateManager = None):
    icon = "star2"
    message = UI_THINKING_MESSAGE

    # Get spinner from state manager if available
    if spinner_obj is None and state_manager:
        spinner_obj = state_manager.session.spinner

    if not spinner_obj:
        spinner_obj = await run_in_terminal(lambda: console.status(message, spinner=icon))
        # Store it back in state manager if available
        if state_manager:
            state_manager.session.spinner = spinner_obj

    if show:
        spinner_obj.start()
    else:
        spinner_obj.stop()

    return spinner_obj


# =============================================================================
# BASE
# =============================================================================


async def panel(
    title: str, text: str, top=1, right=0, bottom=1, left=1, border_style=None, **kwargs
):
    border_style = border_style or kwargs.get("style")
    panel = Panel(Padding(text, 1), title=title, title_align="left", border_style=border_style)
    await print(Padding(panel, (top, right, bottom, left)), **kwargs)


async def print(message, **kwargs):
    await run_in_terminal(lambda: console.print(message, **kwargs))


# =============================================================================
# PANELS
# =============================================================================


async def agent(text: str, bottom=1):
    await panel(APP_NAME, Markdown(text), bottom=bottom, border_style=colors.primary)


async def error(text: str):
    await panel(PANEL_ERROR, text, style=colors.error)


async def dump_messages(messages_list=None, state_manager: StateManager = None):
    if messages_list is None and state_manager:
        # Get messages from state manager
        messages = Pretty(state_manager.session.messages)
    elif messages_list is not None:
        messages = Pretty(messages_list)
    else:
        # No messages available
        messages = Pretty([])
    await panel(PANEL_MESSAGE_HISTORY, messages, style=colors.muted)


async def models(state_manager: StateManager = None):
    model_registry = ModelRegistry()
    model_ids = list(model_registry.list_models().keys())
    model_list = "\n".join([f"{index} - {model}" for index, model in enumerate(model_ids)])
    current_model = state_manager.session.current_model if state_manager else "unknown"
    text = f"Current model: {current_model}\n\n{model_list}"
    await panel(PANEL_MODELS, text, border_style=colors.muted)


async def help():
    """
    Display the available commands.
    """
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


async def tool_confirm(title, content, filepath=None):
    bottom_padding = 0 if filepath else 1
    await panel(title, content, bottom=bottom_padding, border_style=colors.warning)


# Synchronous versions of UI functions for use with run_in_terminal
def sync_print(text, **kwargs):
    console.print(text, **kwargs)


def sync_panel(title, text, top=1, right=0, bottom=1, left=1, border_style=None, **kwargs):
    border_style = border_style or kwargs.get("style")
    panel_obj = Panel(Padding(text, 1), title=title, title_align="left", border_style=border_style)
    console.print(Padding(panel_obj, (top, right, bottom, left)), **kwargs)


def sync_tool_confirm(title, content, filepath=None):
    bottom_padding = 0 if filepath else 1
    sync_panel(title, content, bottom=bottom_padding, border_style=colors.warning)


# =============================================================================
# PRINTS
# =============================================================================


async def info(text: str):
    await print(f"• {text}", style=colors.primary)


async def success(message: str):
    await print(f"• {message}", style=colors.success)


async def warning(text: str):
    await print(f"• {text}", style=colors.warning)


async def muted(text: str, spaces=0):
    await print(f"{' ' * spaces}• {text}", style=colors.muted)


async def usage(usage):
    await print(Padding(usage, (0, 0, 1, 2)), style=colors.muted)


async def version():
    app_settings = ApplicationSettings()
    await info(MSG_VERSION_DISPLAY.format(version=app_settings.version))


async def banner():
    console.clear()
    banner = Padding(BANNER, (1, 0, 0, 2))
    app_settings = ApplicationSettings()
    version = Padding(f"v{app_settings.version}", (0, 0, 1, 2))
    await print(banner, style=colors.primary)
    await print(version, style=colors.muted)


async def clear():
    console.clear()
    await banner()


async def update_available(latest_version):
    await warning(MSG_UPDATE_AVAILABLE.format(latest_version=latest_version))
    await muted(MSG_UPDATE_INSTRUCTION)


# =============================================================================
# I/O
# =============================================================================


async def input(
    session_key: str,
    pretext: str = UI_PROMPT_PREFIX,
    is_password: bool = False,
    validator: Validator = None,
    multiline=False,
    key_bindings=None,
    placeholder=None,
    timeoutlen=0.05,
    state_manager: StateManager = None,
):
    """
    Prompt for user input. Creates session for given key if it doesn't already exist.

    Args:
        session_key (str): The session key for the prompt.
        pretext (str): The text to display before the input prompt.
        is_password (bool): Whether to mask the input.
        state_manager (StateManager): The state manager for session storage.

    """
    if state_manager:
        if session_key not in state_manager.session.input_sessions:
            state_manager.session.input_sessions[session_key] = PromptSession(
                key_bindings=key_bindings,
                placeholder=placeholder,
            )
        prompt_session = state_manager.session.input_sessions[session_key]
    else:
        # Create a temporary session if no state manager
        prompt_session = PromptSession(
            key_bindings=key_bindings,
            placeholder=placeholder,
        )

    try:
        # # Ensure prompt is displayed correctly even after async output
        # await run_in_terminal(lambda: prompt_session.app.invalidate())
        resp = await prompt_session.prompt_async(
            pretext,
            is_password=is_password,
            validator=validator,
            multiline=multiline,
        )
        if isinstance(resp, str):
            resp = resp.strip()
        return resp
    except KeyboardInterrupt:
        raise SidekickAbort
    except EOFError:
        raise SidekickAbort


async def multiline_input():
    placeholder = formatted_text(
        (
            "<darkgrey>"
            "<bold>Enter</bold> to submit, "
            "<bold>Esc + Enter</bold> for new line, "
            "<bold>/help</bold> for commands"
            "</darkgrey>"
        )
    )
    return await input("multiline", key_bindings=kb, multiline=True, placeholder=placeholder)
