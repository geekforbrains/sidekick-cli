from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.validation import ValidationError, Validator
from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from sidekick import config, session
from sidekick.utils.helpers import DotDict

BANNER = """\
███████╗██╗██████╗ ███████╗██╗  ██╗██╗ ██████╗██╗  ██╗
██╔════╝██║██╔══██╗██╔════╝██║ ██╔╝██║██╔════╝██║ ██╔╝
███████╗██║██║  ██║█████╗  █████╔╝ ██║██║     █████╔╝
╚════██║██║██║  ██║██╔══╝  ██╔═██╗ ██║██║     ██╔═██╗
███████║██║██████╔╝███████╗██║  ██╗██║╚██████╗██║  ██╗
╚══════╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝"""


console = Console()
spinner = "star2"
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
# CLASSES & UTILS
# =============================================================================


class UserAbort(Exception):
    pass


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


def line():
    console.line()


def formatted_text(text: str):
    return HTML(text)


# =============================================================================
# PANELS
# =============================================================================


def panel(title: str, text: str, top=1, right=0, bottom=1, left=1, border_style=None, **kwargs):
    border_style = border_style or kwargs.get("style")
    panel = Panel(Padding(text, 1), title=title, title_align="left", border_style=border_style)
    print(Padding(panel, (top, right, bottom, left)), **kwargs)


def agent(text: str, bottom=0):
    panel("Sidekick", Markdown(text), bottom=bottom, border_style=colors.primary)


def error(text: str):
    panel("Error", text, style=colors.error)


def dump_messages():
    messages = Pretty(session.messages)
    panel("Message History", messages, style=colors.muted)


def models():
    model_ids = list(config.MODELS.keys())
    model_list = "\n".join([f"{index} - {model}" for index, model in enumerate(model_ids)])
    text = f"Current model: {session.current_model}\n\n{model_list}"
    panel("Models", text, border_style=colors.muted)


def help():
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

    panel("Available Commands", table, border_style=colors.muted)


# =============================================================================
# PRINTS
# =============================================================================


def print(text: str, **kwargs):
    console.print(text, **kwargs)


def status(text: str):
    print(f"• {text}", style=colors.primary)


def success(message: str):
    print(f"• {message}", style=colors.success)


def warning(text: str):
    print(f"• {text}", style=colors.warning)


def muted(text: str, spaces=0):
    print(f"{' ' * spaces}• {text}", style=colors.muted)


def markdown(text: str):
    return Markdown(text)


def usage(usage):
    print(Padding(usage, (0, 0, 1, 2)), style=colors.muted)


def version():
    status(f"Sidekick CLI {config.VERSION}")


def banner():
    console.clear()
    banner = Padding(BANNER, (1, 0, 0, 2))
    version = Padding(f"v{config.VERSION}", (0, 0, 1, 2))
    print(banner, style=colors.primary)
    print(version, style=colors.muted)


def update_available(latest_version):
    warning(f"Update available: v{latest_version}")
    muted("Exit, and run: [bold]pip install --upgrade sidekick-cli")


# =============================================================================
# I/O
# =============================================================================


async def input(
    session: str,
    pretext: str = "",
    is_password: bool = False,
    validator: Validator = None,
):
    """
    Prompt for user input. Creates session for given key if it doesn't already exist.

    Args:
        session (str): The session name for the prompt.
        pretext (str): The text to display before the input prompt.
        is_password (bool): Whether to mask the input.

    """
    if session not in session.input_sessions:
        session.input_sessions[session] = PromptSession()

    prompt_session = session.input_sessions[session]

    try:
        resp = await prompt_session.prompt_async(
            pretext,
            is_password=is_password,
            validator=validator,
        )
        if isinstance(resp, str):
            resp = resp.strip()
        return resp
    except KeyboardInterrupt:
        raise UserAbort
    except EOFError:
        raise UserAbort
