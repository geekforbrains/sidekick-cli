"""Output and display functions for Sidekick UI."""

from prompt_toolkit.application import run_in_terminal
from rich.padding import Padding

from sidekick.configuration import ApplicationSettings
from sidekick.constants import (MSG_UPDATE_AVAILABLE, MSG_UPDATE_INSTRUCTION, MSG_VERSION_DISPLAY,
                                UI_THINKING_MESSAGE)
from sidekick.types import SessionState
from sidekick.ui.constants import SPINNER_TYPE
from sidekick.ui.decorators import create_sync_wrapper
from sidekick.ui.shared import console, format_bullet_message, format_spaced_message, theme

BANNER = """\
███████╗██╗██████╗ ███████╗██╗  ██╗██╗ ██████╗██╗  ██╗
██╔════╝██║██╔══██╗██╔════╝██║ ██╔╝██║██╔════╝██║ ██╔╝
███████╗██║██║  ██║█████╗  █████╔╝ ██║██║     █████╔╝
╚════██║██║██║  ██║██╔══╝  ██╔═██╗ ██║██║     ██╔═██╗
███████║██║██████╔╝███████╗██║  ██╗██║╚██████╗██║  ██╗
╚══════╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝"""


@create_sync_wrapper
async def print(message, **kwargs) -> None:
    """Print a message to the console."""
    await run_in_terminal(lambda: console.print(message, **kwargs))


async def line() -> None:
    """Print a line to the console."""
    await run_in_terminal(lambda: console.line())


async def info(text: str) -> None:
    """Print an informational message."""
    await print(format_bullet_message(text), style=theme.primary)


async def success(message: str) -> None:
    """Print a success message."""
    await print(format_bullet_message(message), style=theme.success)


@create_sync_wrapper
async def warning(text: str) -> None:
    """Print a warning message."""
    await print(format_bullet_message(text), style=theme.warning)


async def muted(text: str, spaces: int = 0) -> None:
    """Print a muted message."""
    await print(format_spaced_message(text, spaces), style=theme.muted)


async def usage(usage: str) -> None:
    """Print usage information."""
    await print(Padding(usage, (0, 0, 1, 2)), style=theme.muted)


async def version() -> None:
    """Print version information."""
    app_settings = ApplicationSettings()
    await info(MSG_VERSION_DISPLAY.format(version=app_settings.version))


async def banner() -> None:
    """Display the application banner."""
    console.clear()
    banner_padding = Padding(BANNER, (1, 0, 0, 2))
    app_settings = ApplicationSettings()
    version_padding = Padding(f"v{app_settings.version}", (0, 0, 1, 2))
    await print(banner_padding, style=theme.primary)
    await print(version_padding, style=theme.muted)


async def clear() -> None:
    """Clear the console and display the banner."""
    console.clear()
    await banner()


async def update_available(latest_version: str) -> None:
    """Display update available notification."""
    await warning(MSG_UPDATE_AVAILABLE.format(latest_version=latest_version))
    await muted(MSG_UPDATE_INSTRUCTION)


async def spinner(show: bool = True, spinner_obj=None, session: SessionState = None):
    """Manage a spinner display."""
    icon = SPINNER_TYPE
    message = UI_THINKING_MESSAGE

    if spinner_obj is None and session:
        spinner_obj = session.spinner

    if not spinner_obj:
        spinner_obj = await run_in_terminal(lambda: console.status(message, spinner=icon))
        if session:
            session.spinner = spinner_obj

    if show:
        spinner_obj.start()
    else:
        spinner_obj.stop()

    return spinner_obj


# Auto-generated sync versions
sync_print = print.sync  # type: ignore
sync_warning = warning.sync  # type: ignore
