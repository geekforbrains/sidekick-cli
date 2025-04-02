from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty

from sidekick import config, session
from sidekick.utils.helpers import DotDict, ext_to_lang, render_file_diff

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


def panel(title: str, text: str, top=1, right=0, bottom=1, left=1, border_style=None, **kwargs):
    border_style = border_style or kwargs.get("style")
    panel = Panel(Padding(text, 1), title=title, title_align="left", border_style=border_style)
    print(Padding(panel, (top, right, bottom, left)), **kwargs)


def line():
    console.line()


def print(text: str, **kwargs):
    console.print(text, **kwargs)


def agent(text: str, bottom=0):
    panel("Sidekick", Markdown(text), bottom=bottom, border_style=colors.primary)


def status(text: str):
    print(f"• {text}", style=colors.primary)


def success(text: str):
    print(f"• {text}", style=colors.success)


def warning(text: str):
    print(f"• {text}", style=colors.warning)


def error(text: str):
    panel("Error", text, style=colors.error)


def dump_messages():
    messages = Pretty(session.messages)
    panel("Message History", messages, style=colors.muted)


def show_models():
    model_list = "\n".join([f"{index} - {model}" for index, model in enumerate(config.MODELS)])
    text = f"Current model: {session.current_model}\n\n{model_list}"
    panel("Models", text, border_style=colors.muted)


def show_usage(usage):
    print(Padding(usage, (0, 0, 1, 2)), style=colors.muted)


def show_banner():
    console.clear()
    banner = Padding(BANNER, (1, 0, 0, 2))
    version = Padding("v0.1.0", (0, 0, 1, 2))
    print(banner, style=colors.primary)
    print(version, style=colors.secondary)


def render_test():
    # read the contents of hello.py
    with open("hello.py", "r") as file:
        content = file.read()

    content = content.strip()
    code = f"```python\n{content}\n```"
    md = Markdown(code)
    panel("Test", md, border_style=colors.warning)


def _create_code_block(filepath: str, content: str) -> Markdown:
    """
    Create a code block for the given file path and content.

    Args:
        filepath (str): The path to the file.
        content (str): The content of the file.

    Returns:
        Markdown: A Markdown object representing the code block.
    """
    lang = ext_to_lang(filepath)
    code_block = f"```{lang}\n{content}\n```"
    return Markdown(code_block)


def _render_args(tool_name, args):
    """
    Render the tool arguments for a given tool.

    """
    # Show diff between `target` and `patch` on file updates
    if tool_name == "update_file":
        return render_file_diff(args["target"], args["patch"], colors)

    # Show file content on read_file
    elif tool_name == "write_file":
        return _create_code_block(args["filepath"], args["content"])

    # Default to showing key and value on new line
    content = ""
    for key, value in args.items():
        if isinstance(value, list):
            content += f"{key}\n"
            for item in value:
                content += f"  - {item}\n"
            content += "\n"
        else:
            content += f"{key}\n{value}\n\n"
    return content.strip()


def confirm(tool_call, node):
    # If we're in yolo mode, skip all confirmations
    if session.yolo:
        return

    # If tool in session ignore list, skip confirmation
    if tool_call.tool_name in session.tool_ignore:
        return

    # If tool in user config ignore list, skip confirmation
    if tool_call.tool_name in session.user_config["settings"]["tool_ignore"]:
        return

    session.spinner.stop()
    title = f"Tool({tool_call.tool_name})"
    content = _render_args(tool_call.tool_name, tool_call.args)
    panel(title, content, border_style=colors.warning)
    resp = input("  Continue? (y/N/(i)gnore): ")

    if resp.lower() == "i":
        session.tool_ignore.append(tool_call.tool_name)

    elif resp.lower() != "y":
        raise UserAbort("User aborted.")

    session.spinner.start()
