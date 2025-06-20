import random

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from sidekick.constants import APP_NAME, APP_VERSION
from sidekick.session import session
from sidekick.tools import TOOL_DISPLAY_NAMES

console = Console()


# Color scheme from main branch
class Colors:
    primary = "medium_purple1"
    secondary = "medium_purple3"
    success = "green"
    warning = "orange1"
    error = "red"
    muted = "grey62"


colors = Colors()

BANNER = """
███████╗██╗██████╗ ███████╗██╗  ██╗██╗ ██████╗██╗  ██╗
██╔════╝██║██╔══██╗██╔════╝██║ ██╔╝██║██╔════╝██║ ██╔╝
███████╗██║██║  ██║█████╗  █████╔╝ ██║██║     █████╔╝
╚════██║██║██║  ██║██╔══╝  ██╔═██╗ ██║██║     ██╔═██╗
███████║██║██████╔╝███████╗██║  ██╗██║╚██████╗██║  ██╗
╚══════╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝"""

THINKING_MESSAGES = [
    "Cracking knuckles...",
    "Polishing grappling hook...",
    "Consulting the manual...",
    "Adjusting utility belt...",
    "Calibrating gadgets...",
    "Dusting off cape...",
    "Sharpening batarangs...",
    "Pressing buttons...",
    "Looking busy...",
    "Doing stretches...",
    "Putting on thinking mask...",
    "Running diagnostics...",
    "Preparing witty comeback...",
    "Calculating trajectories...",
    "Donning thinking cape...",
]


def get_thinking_message() -> str:
    """Get a random thinking message."""
    return random.choice(THINKING_MESSAGES)


# Style definitions
class SpinnerStyle:
    DEFAULT = f"[bold {colors.primary}]{{}}[/bold {colors.primary}]"
    MUTED = f"[{colors.muted}]{{}}[/{colors.muted}]"
    WARNING = f"[{colors.warning}]{{}}[/{colors.warning}]"
    ERROR = f"[{colors.error}]{{}}[/{colors.error}]"


def banner():
    """Display the application banner."""
    console.clear()
    banner_padding = Padding(BANNER, (1, 0, 0, 2))
    version_padding = Padding(f"v{APP_VERSION}", (0, 0, 1, 2))
    console.print(banner_padding, style=colors.primary)
    console.print(version_padding, style=colors.muted)


def info(message: str):
    """Display an info message."""
    console.print(f"• {message}", style=colors.primary)


def error(message: str, detail: str = None):
    """Display an error message with optional detail.

    Args:
        message: The main error message
        detail: Optional detailed error information
    """
    if detail:
        panel = Panel(
            Padding(f"{message}\n\n{detail}", 1),
            title="Error",
            title_align="left",
            border_style=colors.error,
        )
    else:
        panel = Panel(
            Padding(message, 1), title="Error", title_align="left", border_style=colors.error
        )
    console.print(Padding(panel, (1, 0, 1, 1)))


def warning(message: str):
    """Display a warning message."""
    console.print(f"• {message}", style=colors.warning)


def success(message: str):
    """Display a success message."""
    console.print(f"• {message}", style=colors.success)


def bullet(message: str):
    """Display a bulleted list item."""
    console.print(f"  • {message}", style=colors.muted)


def muted(message: str, spaces: int = 0):
    """Display a muted message."""
    console.print(f"{' ' * spaces}• {message}", style=colors.muted)


def agent(content: str):
    """Display agent output with markdown formatting."""
    panel = Panel(
        Padding(Markdown(content), 1),
        title="Sidekick",
        title_align="left",
        border_style=colors.primary,
    )
    console.print(Padding(panel, (1, 0, 0, 1)))


def line():
    """Print a simple line separator."""
    console.print()


def dump(data):
    """Display data in a formatted panel."""
    pretty = Pretty(data, expand_all=True)
    panel = Panel(
        Padding(pretty, 1), title="Message History", title_align="left", border_style=colors.muted
    )
    console.print(Padding(panel, (1, 0, 1, 1)))


def format_tool_name(tool_name: str) -> str:
    """Format tool name for display."""
    if tool_name in TOOL_DISPLAY_NAMES:
        return TOOL_DISPLAY_NAMES[tool_name]
    else:
        return f"MCP({tool_name})"


async def confirm_tool_call(tool_name: str, args: dict) -> str:
    """
    Prompt user for confirmation before executing a tool.

    Returns:
        'yes' - Execute this tool
        'always' - Execute this tool and don't ask again for this tool type
        'no' - Cancel this tool execution
    """
    formatted_name = format_tool_name(tool_name)
    content_lines = [f"Tool: [bold]{formatted_name}[/bold]", ""]

    for key, value in args.items():
        if isinstance(value, str):
            value = value.strip()
            if len(value) > 100:
                value = value[:97] + "..."
        content_lines.append(f"• {key}: {value}")

    # Determine the "always" option text based on tool type
    if tool_name == "run_command" and "command" in args:
        from sidekick.utils.command_parser import extract_commands

        commands = extract_commands(args["command"])
        if len(commands) > 1:
            always_text = f"  a - Always allow: {', '.join(commands)}"
        else:
            always_text = (
                f"  a - Always allow '{commands[0]}' commands"
                if commands
                else "  a - Always allow this command"
            )
    else:
        always_text = "  a - Always allow this tool"

    content_lines.extend(
        [
            "",
            "Options:",
            "  y - Yes, execute this tool",
            always_text,
            "  n - No, cancel this execution",
        ]
    )

    content = "\n".join(content_lines)
    panel = Panel(
        Padding(content, 1), title="Confirm Action", title_align="left", border_style=colors.warning
    )
    console.print(Padding(panel, (1, 0, 1, 1)))

    while True:
        choice = (
            console.input(
                f"  [{colors.warning}]Continue?[/{colors.warning}] [y/a/n] (default: y): "
            )
            .lower()
            .strip()
        )

        if choice == "" or choice in ["y", "yes"]:
            return "yes"
        elif choice in ["a", "always"]:
            return "always"
        elif choice in ["n", "no"]:
            return "no"
        else:
            console.print("  Invalid choice. Please enter y, a, or n.", style=colors.error)


def start_spinner(message: str, style: str = SpinnerStyle.DEFAULT):
    """Start a spinner and store it in session."""
    formatted_message = style.format(message)
    session.spinner = console.status(formatted_message, spinner="star2")
    session.spinner.start()


def stop_spinner():
    """Stop and clear the session spinner."""
    if session.spinner:
        session.spinner.stop()
        session.spinner = None


def help():
    """Display the available commands."""
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
        ("/usage", "Show session usage statistics"),
        ("exit", "Exit the application"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    panel = Panel(
        Padding(table, 1), title="Available Commands", title_align="left", border_style=colors.muted
    )
    console.print(Padding(panel, (1, 0, 1, 1)))


def version():
    """Display version information."""
    console.print(f"• {APP_NAME} v{APP_VERSION}", style=colors.primary)


def update_available(latest_version: str):
    """Display update available message."""
    warning(f"Update available: v{latest_version}")
    muted("Exit, and run: [bold]pip install --upgrade sidekick-cli[/bold]", spaces=2)


def usage(usage_data: dict):
    """Display usage information in the compact format."""
    if not usage_data:
        return

    msg = (
        f"Reqs: {usage_data['requests']}, "
        f"Tokens(In/Cache/Out): "
        f"{usage_data['input_tokens']}/"
        f"{usage_data['cached_tokens']}/"
        f"{usage_data['output_tokens']}, "
        f"Cost(Req/Total): ${usage_data['request_cost']:.5f}/${usage_data['total_cost']:.5f}"
    )

    # Display aligned with panel content, with padding below
    console.print(f"  {msg}", style=colors.muted)
    console.print()
