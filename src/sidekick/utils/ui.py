import json

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from sidekick import config, session
from sidekick.utils.helpers import DotDict, ext_to_lang, key_to_title, render_file_diff

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


def muted(text: str, spaces=0):
    # print(f"• {text}", style=colors.muted)
    print(f"{' ' * spaces}• {text}", style=colors.muted)


def error(text: str):
    panel("Error", text, style=colors.error)


def dump_messages():
    messages = Pretty(session.messages)
    panel("Message History", messages, style=colors.muted)


def show_models():
    model_ids = list(config.MODELS.keys())
    model_list = "\n".join([f"{index} - {model}" for index, model in enumerate(model_ids)])
    text = f"Current model: {session.current_model}\n\n{model_list}"
    panel("Models", text, border_style=colors.muted)


def show_usage(usage):
    print(Padding(usage, (0, 0, 1, 2)), style=colors.muted)


def show_banner():
    console.clear()
    banner = Padding(BANNER, (1, 0, 0, 2))
    version = Padding(f"v{config.VERSION}", (0, 0, 0, 2))
    commands = Padding("Esc + Enter to submit, /help for commands", (0, 0, 1, 2))
    print(banner, style=colors.primary)
    print(version, style=colors.muted)
    print(commands, style=colors.muted)


def show_help():
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
        ("/model <name>", "Switch to a specific model"),
        ("exit", "Exit the application"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    panel("Available Commands", table, border_style=colors.muted)


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
            content += f"{key_to_title(key)}:\n"
            for item in value:
                content += f"  - {item}\n"
            content += "\n"
        else:
            # If string length is over 200 characters
            # split to new line
            # content += f"{key.title()}:\n{value}\n\n"
            value = str(value)
            content += f"{key_to_title(key)}:"
            if len(value) > 200:
                content += f"\n{value}\n\n"
            else:
                content += f" {value}\n\n"
    return content.strip()


def _parse_args(args):
    """
    Parse tool arguments from a JSON string or dictionary.

    Args:
        args (str or dict): A JSON-formatted string or a dictionary containing tool arguments.

    Returns:
        dict: The parsed arguments.

    Raises:
        ValueError: If 'args' is not a string or dictionary, or if the string is not valid JSON.
    """
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON: {args}")
    elif isinstance(args, dict):
        return args
    else:
        raise ValueError(f"Invalid args type: {type(args)}")


def _log_mcp(title, args):
    """
    Checks if the tool call is an MCP and displays it's information.

    Returns a list of args as a string

    Example: {"foo": "bar", "baz": "qux"} => foo: bar, baz: qux

    Args:
        args (dict): The arguments for the tool call.
    """
    if not args:
        return

    status(title)
    for key, value in args.items():
        if isinstance(value, list):
            value = ", ".join(value)
        muted(f"{key}: {value}", spaces=4)


def _get_tool_title(tool_name):
    """
    Checks if the tool exists within this system. If it does
    it return "Tool" otherwise assumed to be an MCP so returns "MCP"
    """
    if tool_name in config.INTERNAL_TOOLS:
        return f"Tool({tool_name})"
    else:
        return f"MCP({tool_name})"


def confirm(tool_call, node):
    title = _get_tool_title(tool_call.tool_name)
    args = _parse_args(tool_call.args)

    # If we're skipping confirmation on this tool, log its output if MCP
    if (
        session.yolo
        or tool_call.tool_name in session.tool_ignore
        or tool_call.tool_name in session.user_config["settings"]["tool_ignore"]
    ):
        if tool_call.tool_name not in config.INTERNAL_TOOLS:
            _log_mcp(title, args)
        return

    session.spinner.stop()
    content = _render_args(tool_call.tool_name, args)
    filepath = args.get("filepath")

    # Set bottom padding to 0 if filepath is not None
    bottom_padding = 0 if filepath else 1

    panel(title, content, bottom=bottom_padding, border_style=colors.warning)

    # If tool call has filepath, show it under panel
    if filepath:
        show_usage(f"File: {filepath}")

    print("  1. Yes (default)")
    print("  2. Yes, and don't ask again for commands like this")
    print("  3. No, and tell Sidekick what to do differently")
    resp = input("  Choose an option [1/2/3]: ").strip() or "1"

    if resp == "2":
        session.tool_ignore.append(tool_call.tool_name)
    elif resp == "3":
        raise UserAbort("User aborted.")

    session.spinner.start()
