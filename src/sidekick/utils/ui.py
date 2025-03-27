from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty

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


class UserAbort(Exception):
    pass


def _panel(title: str, text: str, top=1, right=0, bottom=1, left=1, border_style=None, **kwargs):
    border_style = border_style or kwargs.get("style")
    panel = Panel(Padding(text, 1), title=title, title_align="left", border_style=border_style)
    print(Padding(panel, (top, right, bottom, left)), **kwargs)


def print(text: str, **kwargs):
    console.print(text, **kwargs)


def agent(text: str, bottom=0):
    _panel("Sidekick", Markdown(text), bottom=bottom, border_style=colors.primary)


def status(text: str):
    print(f"• {text}", style=colors.primary)


def success(text: str):
    print(f"• {text}", style=colors.success)


def warning(text: str):
    print(f"• {text}", style=colors.warning)


def error(text: str):
    _panel("Error", text, style=colors.error)


def dump_messages():
    messages = Pretty(session.messages)
    _panel("Message History", messages, style=colors.muted)


def show_models():
    model_list = "\n".join([f"{index} - {model}" for index, model in enumerate(config.models)])
    text = f"Current model: {session.current_model}\n\n{model_list}"
    _panel("Models", text, border_style=colors.muted)


def show_usage(usage):
    print(Padding(usage, (0, 0, 1, 2)), style=colors.muted)


def show_banner():
    console.clear()
    banner = Padding(BANNER, (1, 0, 0, 2))
    version = Padding("v0.1.0", (0, 0, 1, 2))
    print(banner, style=colors.primary)
    print(version, style=colors.secondary)


def confirm(tool_call, node):
    if session.yolo or tool_call.tool_name in session.tool_ignore:
        return

    session.spinner.stop()
    title = f"Tool({tool_call.tool_name})"
    content = "\n".join(v for v in tool_call.args.values()).strip()
    _panel(title, Pretty(content), style=colors.warning)
    resp = input("  Continue? (y/N/(i)gnore): ")

    if resp.lower() == "i":
        session.tool_ignore.append(tool_call.tool_name)

    elif resp.lower() != "y":
        raise UserAbort("User aborted.")

    session.spinner.start()
