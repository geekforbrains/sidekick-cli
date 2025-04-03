import re
from pathlib import Path

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
    version = Padding("v0.1.0", (0, 0, 1, 2))
    print(banner, style=colors.primary)
    print(version, style=colors.secondary)


def show_help():
    """
    Display the available commands from the README.md file.
    This function dynamically reads the README to ensure the help text
    stays in sync with the documentation.
    """
    # Find the project root directory
    root_dir = Path(__file__).resolve().parents[3]
    readme_path = root_dir / "README.md"

    try:
        with open(readme_path, "r") as f:
            readme_content = f.read()

        # Extract the commands section
        commands_match = re.search(r"### Available Commands\s+([\s\S]+?)(?=##|\Z)", readme_content)

        if commands_match:
            commands_text = commands_match.group(1).strip()
            # Extract individual commands with their descriptions
            command_pattern = r"`(.*?)`\s*-\s*(.*)"
            command_matches = re.findall(command_pattern, commands_text)

            # Create a table for nicer formatting
            table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
            table.add_column("Command", style="white", justify="right")
            table.add_column("Description", style="white")

            # Add each command to the table
            for cmd, desc in command_matches:
                table.add_row(cmd, desc)

            # Create panel with title and the table
            panel("Available Commands", table, border_style=colors.muted)
        else:
            warning("Could not find commands section in README.md")
    except Exception as e:
        error(f"Error reading commands from README: {str(e)}")


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
