from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty
from rich.text import Text

from sidekick import session
from sidekick.constants import APP_NAME, APP_VERSION

console = Console()


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


async def error(message: str):
    """Display an error message."""
    console.print(f"[red]✗[/red] {message}", style="red")


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
