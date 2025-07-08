"""Status message functions."""

from rich.console import Console
from rich.padding import Padding
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

from sidekick.constants import APP_NAME, APP_VERSION, MODELS
from sidekick.session import session
from sidekick.ui import panels
from sidekick.ui.colors import colors
from sidekick.usage import usage_tracker

console = Console()


def info(message: str):
    """Display an info message."""
    panels._prepare_to_print("status")
    console.print(f"• {message}", style=colors.primary)
    panels._last_output = "status"


def thinking(message: str):
    """Display an agent thinking message with proper indentation for multi-line content."""
    panels._prepare_to_print("status")
    lines = message.strip().split("\n")
    if lines:
        console.print(f"› {lines[0]}", style=colors.muted)
        for line in lines[1:]:
            console.print(f"  {line}", style=colors.muted)
    panels._last_output = "status"


def error(message: str, detail: str = None):
    """Display an error message."""
    panels._prepare_to_print("status")
    if detail:
        console.print(f"✗ {message}: {detail}", style=colors.error)
    else:
        console.print(f"✗ {message}", style=colors.error)
    panels._last_output = "status"


def warning(message: str):
    """Display a warning message."""
    panels._prepare_to_print("status")
    console.print(f"⚠ {message}", style=colors.warning)
    panels._last_output = "status"


def success(message: str):
    """Display a success message."""
    panels._prepare_to_print("status")
    console.print(f"✓ {message}", style=colors.success)
    panels._last_output = "status"


def bullet(message: str):
    """Display a bullet point message."""
    panels._prepare_to_print("status")
    console.print(f"  - {message}", style=colors.muted)
    panels._last_output = "status"


def muted(message: str, spaces: int = 0):
    """Display a muted message."""
    panels._prepare_to_print("status")
    console.print(f"{' ' * spaces}{message}", style=colors.muted)
    panels._last_output = "status"


def agent(content: str, has_footer: bool = False):
    """Display agent response."""
    # Just use the display_agent_panel function from panels
    panels.display_agent_panel(content, has_footer)


def line():
    """Print a blank line."""
    console.print()


def dump(data):
    """Display data in a pretty format."""
    console.print(Pretty(data))


def help():
    """Display help information."""
    commands = [
        ("/help", "Show this help message"),
        ("/yolo", "Toggle tool confirmation prompts"),
        ("/clear", "Clear conversation history"),
        ("/model", "List available models"),
        ("/model <num>", "Switch to a specific model"),
        ("/model <num> default", "Set a model as default"),
        ("/usage", "Show session usage statistics"),
        ("exit", "Exit the application"),
    ]

    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    table.add_column("Command", style=colors.primary, no_wrap=True)
    table.add_column("Description", style="white")

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    panels.display_info_panel(table, "Available Commands")


def version():
    """Display version information."""
    console.print(f"{APP_NAME} v{APP_VERSION}", style=colors.muted)


def update_available(latest_version: str):
    """Display update available message."""
    muted(f"Update available: {APP_VERSION} → {latest_version}")


def usage(usage_data: dict):
    """Display usage statistics."""
    content = Text()
    content.append("Input: ", style=colors.muted)
    content.append(f"{usage_data['input_tokens']:,} tokens")
    if usage_data["cached_tokens"] > 0:
        content.append(f" ({usage_data['cached_tokens']:,} cached)", style=colors.muted)

    content.append(" | ", style=colors.muted)
    content.append("Output: ", style=colors.muted)
    content.append(f"{usage_data['output_tokens']:,} tokens")

    content.append(" | ", style=colors.muted)
    content.append("Cost: ", style=colors.muted)
    content.append(f"${usage_data['request_cost']:.5f}")

    if session.current_model and usage_tracker.total_tokens:
        model_info = MODELS.get(session.current_model)
        if model_info and "context_window" in model_info:
            token_limit = model_info["context_window"]
            if token_limit > 0:
                remaining_percentage = (
                    (token_limit - usage_tracker.total_tokens) / token_limit
                ) * 100
                # Ensure percentage doesn't go below 0 (can happen if total_tokens exceeds limit)
                remaining_percentage = max(0, remaining_percentage)
                content.append(" | ", style=colors.muted)
                content.append(f"{remaining_percentage:.0f}% ")
                content.append("Context remaining", style=colors.muted)

    console.print(Padding(content, (0, 0, 0, 2)))
