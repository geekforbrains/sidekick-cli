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

from sidekick import config, session
from sidekick.exceptions import SidekickAbort
from sidekick.utils.helpers import DotDict

BANNER = """\
███████╗██╗██████╗ ███████╗██╗  ██╗██╗ ██████╗██╗  ██╗
██╔════╝██║██╔══██╗██╔════╝██║ ██╔╝██║██╔════╝██║ ██╔╝
███████╗██║██║  ██║█████╗  █████╔╝ ██║██║     █████╔╝
╚════██║██║██║  ██║██╔══╝  ██╔═██╗ ██║██║     ██╔═██╗
███████║██║██████╔╝███████╗██║  ██╗██║╚██████╗██║  ██╗
╚══════╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝"""


console = Console()
colors = DotDict(
    {
        "primary": "medium_purple1",
        "secondary": "medium_purple3",
        "success": "green",
        "warning": "orange1",
        "error": "red",
        "muted": "grey62",
    }
)


# =============================================================================
# KEY BINDINGS
# =============================================================================


kb = KeyBindings()


@kb.add("escape", eager=True)
def _cancel(event):
    """Kill the running agent task, if any."""
    if session.current_task and not session.current_task.done():
        session.current_task.cancel()
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


async def spinner(show=True):
    icon = "star2"
    message = "[bold green]Thinking..."

    if not session.spinner:
        session.spinner = await run_in_terminal(lambda: console.status(message, spinner=icon))

    if show:
        session.spinner.start()
    else:
        session.spinner.stop()
        session.spinner = None

        for prompt_session in session.input_sessions.values():
            await run_in_terminal(lambda: prompt_session.app.invalidate())


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
    await panel("Sidekick", Markdown(text), bottom=bottom, border_style=colors.primary)


async def error(text: str):
    await panel("Error", text, style=colors.error)


async def dump_messages():
    messages = Pretty(session.messages)
    await panel("Message History", messages, style=colors.muted)


async def models():
    model_ids = list(config.MODELS.keys())
    model_list = "\n".join([f"{index} - {model}" for index, model in enumerate(model_ids)])
    text = f"Current model: {session.current_model}\n\n{model_list}"
    await panel("Models", text, border_style=colors.muted)


async def help():
    """
    Display the available commands.
    """
    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    table.add_column("Command", style="white", justify="right")
    table.add_column("Description", style="white")

    commands = [
        ("/help", "Show this help message"),
        ("/clear", "Clear the conversation history"),
        ("/dump", "Show the current conversation history"),
        ("/yolo", "Toggle confirmation prompts on/off"),
        ("/undo", "Undo the last file change"),
        ("/compact", "Summarize the conversation context"),
        ("/model", "List available models"),
        ("/model <n>", "Switch to a specific model"),
        ("/model <n> default", "Set a model as the default"),
        ("exit", "Exit the application"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    await panel("Available Commands", table, border_style=colors.muted)


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
    await info(f"Sidekick CLI {config.VERSION}")


async def banner():
    console.clear()
    banner = Padding(BANNER, (1, 0, 0, 2))
    version = Padding(f"v{config.VERSION}", (0, 0, 1, 2))
    await print(banner, style=colors.primary)
    await print(version, style=colors.muted)


async def update_available(latest_version):
    await warning(f"Update available: v{latest_version}")
    await muted("Exit, and run: [bold]pip install --upgrade sidekick-cli")


# =============================================================================
# I/O
# =============================================================================


async def input(
    session_key: str,
    pretext: str = "λ ",
    is_password: bool = False,
    validator: Validator = None,
    multiline=False,
    key_bindings=None,
    placeholder=None,
    timeoutlen=0.05,
):
    """
    Prompt for user input. Creates session for given key if it doesn't already exist.

    Args:
        session (str): The session name for the prompt.
        pretext (str): The text to display before the input prompt.
        is_password (bool): Whether to mask the input.

    """
    if session_key not in session.input_sessions:
        session.input_sessions[session_key] = PromptSession(
            key_bindings=key_bindings,
            placeholder=placeholder,
        )

    prompt_session = session.input_sessions[session_key]

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
