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

# Padding constants for consistent spacing
PANEL_CONTENT_PADDING = 1
PANEL_WRAPPER_PADDING = (1, 0, 1, 1)
PANEL_WRAPPER_PADDING_NO_BOTTOM = (1, 0, 0, 1)


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


def create_panel(content, title: str, border_style: str):
    """Create a panel with consistent padding and alignment.

    Args:
        content: The content to display in the panel
        title: Panel title
        border_style: Border color style

    Returns:
        Panel object with consistent configuration
    """
    return Panel(
        Padding(content, PANEL_CONTENT_PADDING),
        title=title,
        title_align="left",
        border_style=border_style,
    )


def display_panel(panel, bottom_padding: bool = True):
    """Display a panel with consistent wrapper padding.

    Args:
        panel: The panel to display
        bottom_padding: Whether to include bottom padding (default: True)
    """
    padding = PANEL_WRAPPER_PADDING if bottom_padding else PANEL_WRAPPER_PADDING_NO_BOTTOM
    console.print(Padding(panel, padding))


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
    content = f"{message}\n\n{detail}" if detail else message
    panel = create_panel(content, "Error", colors.error)
    display_panel(panel)


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
    panel = create_panel(Markdown(content), "Sidekick", colors.primary)
    display_panel(panel, bottom_padding=False)


def line():
    """Print a simple line separator."""
    console.print()


def dump(data):
    """Display data in a formatted panel."""
    pretty = Pretty(data, expand_all=True)
    panel = create_panel(pretty, "Message History", colors.muted)
    display_panel(panel)


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
    panel = create_panel(content, "Confirm Action", colors.warning)
    display_panel(panel)

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

    panel = create_panel(table, "Available Commands", colors.muted)
    display_panel(panel)


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
