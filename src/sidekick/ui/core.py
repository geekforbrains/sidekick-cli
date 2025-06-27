"""Core UI functions including banner and spinner management."""

import asyncio
import random

from rich.console import Console
from rich.padding import Padding

from sidekick.constants import APP_VERSION
from sidekick.session import session
from sidekick.ui.panels import Colors

console = Console()
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


# Style definitions
class SpinnerStyle:
    DEFAULT = f"[bold {colors.primary}]{{}}[/bold {colors.primary}]"
    MUTED = f"[{colors.muted}]{{}}[/{colors.muted}]"
    WARNING = f"[{colors.warning}]{{}}[/{colors.warning}]"
    ERROR = f"[{colors.error}]{{}}[/{colors.error}]"


def get_thinking_message() -> str:
    """Get a random thinking message."""
    return random.choice(THINKING_MESSAGES)


async def _rotate_thinking_messages(style: str, interval: float = 5.0):
    """Rotate thinking messages at specified interval."""
    while True:
        try:
            await asyncio.sleep(interval)
            if session.spinner:
                message = get_thinking_message()
                formatted_message = style.format(message)
                session.spinner.update(formatted_message)
        except asyncio.CancelledError:
            break
        except Exception:
            break


def banner():
    """Display the application banner."""
    from sidekick.ui import panels

    console.clear()
    banner_padding = Padding(BANNER, (1, 0, 0, 2))
    version_padding = Padding(f"v{APP_VERSION}", (0, 0, 1, 2))
    console.print(banner_padding, style=colors.primary)
    console.print(version_padding, style=colors.muted)
    panels._last_output = None  # Reset context after banner


def start_spinner(message: str, style: str = SpinnerStyle.DEFAULT):
    """Start the spinner with a message."""
    formatted_message = style.format(message)
    session.spinner = console.status(formatted_message, spinner="dots")
    session.spinner.start()

    # Start rotation task
    if session.spinner_rotation_task:
        session.spinner_rotation_task.cancel()
    session.spinner_rotation_task = asyncio.create_task(_rotate_thinking_messages(style))


def stop_spinner():
    """Stop the spinner."""
    if session.spinner:
        session.spinner.stop()
        session.spinner = None

    if session.spinner_rotation_task:
        session.spinner_rotation_task.cancel()
        session.spinner_rotation_task = None
