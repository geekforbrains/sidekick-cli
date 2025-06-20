import random

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from rich.text import Text

from sidekick import session
from sidekick.constants import APP_NAME, APP_VERSION

console = Console()

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
    "Calculating trajenctories...",
    "Donning thinking cape...",
]


def get_thinking_message() -> str:
    """Get a random thinking message."""
    return random.choice(THINKING_MESSAGES)


# Style definitions
class SpinnerStyle:
    DEFAULT = "[bold cyan]{}[/bold cyan]"
    MUTED = "[dim]{}[/dim]"
    WARNING = "[yellow]{}[/yellow]"
    ERROR = "[red]{}[/red]"


async def banner():
    """Display the application banner."""
    banner_text = Text()
    banner_text.append(f"{APP_NAME}\n", style="bold cyan")
    banner_text.append(f"v{APP_VERSION}", style="dim")

    console.print(Panel(banner_text, border_style="cyan", padding=(1, 2)))
    console.print()


async def info(message: str):
    """Display an info message."""
    console.print(f"[cyan]ℹ[/cyan] {message}")


async def error(message: str, detail: str = None):
    """Display an error message with optional detail.

    Args:
        message: The main error message
        detail: Optional detailed error information
    """
    console.print(f"[red]✗[/red] [red]{message}[/red]")
    if detail:
        console.print(f"  [dim]{detail}[/dim]")


async def warning(message: str):
    """Display a warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")


async def success(message: str):
    """Display a success message."""
    console.print(f"[green]✓[/green] {message}")


async def bullet(message: str):
    """Display a bulleted list item."""
    console.print(f"  [dim]•[/dim] {message}")


async def muted(message: str):
    """Display a muted message."""
    console.print(message, style="dim")


async def agent(content: str):
    """Display agent output with markdown formatting."""
    console.print()
    console.print(Markdown(content))
    console.print()


async def line():
    """Print a simple line separator."""
    console.print()


async def dump(data):
    pretty = Pretty(data, expand_all=True)
    panel = Panel(pretty, title="Dumped Data", border_style="blue", padding=(1, 2))
    console.print(panel)


async def confirm_tool_call(tool_name: str, args: dict) -> str:
    """
    Prompt user for confirmation before executing a tool.

    Returns:
        'yes' - Execute this tool
        'always' - Execute this tool and don't ask again for this tool type
        'no' - Cancel this tool execution
    """
    console.print()
    console.print(f"[yellow]⚠[/yellow]  Tool execution requested: [bold]{tool_name}[/bold]")

    # Display arguments in a nice format
    for key, value in args.items():
        if isinstance(value, str):
            value = value.strip()
            if len(value) > 100:
                value = value[:97] + "..."
        console.print(f"   [dim]•[/dim] {key}: {value}")

    console.print()
    console.print("Options:")
    console.print("  [green]y[/green] - Yes, execute this tool")
    console.print("  [cyan]a[/cyan] - Always allow this tool (don't ask again)")
    console.print("  [red]n[/red] - No, cancel this execution")
    console.print()

    while True:
        choice = (
            console.input(
                "[yellow]Continue?[/yellow] [[green]y[/green]/[cyan]a[/cyan]/[red]n[/red]]: "
            )
            .lower()
            .strip()
        )

        if choice in ["y", "yes"]:
            return "yes"
        elif choice in ["a", "always"]:
            return "always"
        elif choice in ["n", "no"]:
            return "no"
        else:
            console.print("[red]Invalid choice. Please enter y, a, or n.[/red]")


def start_spinner(message: str, style: str = SpinnerStyle.DEFAULT):
    """Start a spinner and store it in session."""
    formatted_message = style.format(message)
    session.spinner = console.status(formatted_message, spinner="dots")
    session.spinner.start()


def stop_spinner():
    """Stop and clear the session spinner."""
    if session.spinner:
        session.spinner.stop()
        session.spinner = None
