"""Shared UI utilities and patterns for Sidekick."""

from typing import Any, Optional, Union

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty

from sidekick.constants import UI_COLORS
from sidekick.ui.constants import DEFAULT_PANEL_PADDING
from sidekick.utils.file_utils import DotDict

# Shared color theme
colors = DotDict(UI_COLORS)

# Shared console instance
console = Console()


def create_padded_panel(
    title: str,
    content: Union[str, Markdown, Pretty],
    border_style: Optional[str] = None,
    padding_top: int = DEFAULT_PANEL_PADDING["top"],
    padding_right: int = DEFAULT_PANEL_PADDING["right"],
    padding_bottom: int = DEFAULT_PANEL_PADDING["bottom"],
    padding_left: int = DEFAULT_PANEL_PADDING["left"],
    inner_padding: int = 1,
    **kwargs: Any,
) -> Panel:
    """
    Create a consistently formatted panel with padding.

    Args:
        title: Panel title
        content: Panel content
        border_style: Border color/style
        padding_top: Top outer padding
        padding_right: Right outer padding
        padding_bottom: Bottom outer padding
        padding_left: Left outer padding
        inner_padding: Inner content padding
        **kwargs: Additional panel arguments

    Returns:
        Panel: Formatted rich Panel object
    """
    panel_obj = Panel(
        Padding(content, inner_padding),
        title=title,
        title_align="left",
        border_style=border_style,
        **kwargs,
    )
    return Padding(panel_obj, (padding_top, padding_right, padding_bottom, padding_left))


def format_bullet_message(text: str, style: Optional[str] = None) -> str:
    """
    Format a message with a bullet point prefix.

    Args:
        text: Message text
        style: Optional style for the message

    Returns:
        str: Formatted message with bullet
    """
    return f"• {text}"


def format_spaced_message(text: str, spaces: int = 0) -> str:
    """
    Format a message with leading spaces and bullet.

    Args:
        text: Message text
        spaces: Number of leading spaces

    Returns:
        str: Formatted message with spaces and bullet
    """
    return f"{' ' * spaces}• {text}"


class UITheme:
    """Centralized UI theme and styling utilities."""

    def __init__(self):
        self.colors = colors

    @property
    def primary(self) -> str:
        return self.colors.primary

    @property
    def secondary(self) -> str:
        return self.colors.secondary

    @property
    def success(self) -> str:
        return self.colors.success

    @property
    def warning(self) -> str:
        return self.colors.warning

    @property
    def error(self) -> str:
        return self.colors.error

    @property
    def muted(self) -> str:
        return self.colors.muted


# Shared theme instance
theme = UITheme()
