"""Panel creation and display functions."""

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.text import Text

from sidekick.ui.colors import colors

console = Console()

# Padding constants for consistent spacing
PANEL_CONTENT_PADDING = 1
PANEL_WRAPPER_PADDING = (0, 0, 1, 1)  # Standard panel padding (left indent)
PANEL_WRAPPER_PADDING_NO_BOTTOM = (0, 0, 0, 1)  # Used for panels with footers

# Track last output type for consistent spacing
_last_output = None  # "status", "panel", "user_input", or None


def _prepare_to_print(new_type: str):
    """Adds a blank line if needed based on context."""
    if _last_output is None or _last_output == "user_input":
        return

    # Add space when switching from a panel to a status message.
    if new_type == "status" and _last_output == "panel":
        console.print()
    # Add space when switching from status to a panel, or panel to panel.
    elif new_type == "panel" and (_last_output == "status" or _last_output == "panel"):
        console.print()


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


def display_panel(panel):
    """Display a panel with consistent padding."""
    global _last_output
    _prepare_to_print("panel")
    console.print(Padding(panel, PANEL_WRAPPER_PADDING))
    _last_output = "panel"


def display_agent_panel(content: str, has_footer: bool = False):
    """Display agent response panel with specific padding."""
    global _last_output
    _prepare_to_print("panel")
    panel = create_panel(Markdown(content), "Sidekick", colors.primary)
    padding = PANEL_WRAPPER_PADDING_NO_BOTTOM if has_footer else PANEL_WRAPPER_PADDING
    console.print(Padding(panel, padding))
    _last_output = "panel"


def display_tool_panel(content, title: str, footer: str = None):
    """Display tool data panel with optional footer."""
    global _last_output
    _prepare_to_print("panel")
    panel = create_panel(content, title, colors.tool_data)

    # Always use no bottom padding for tool panels since they're followed by confirmation options
    console.print(Padding(panel, PANEL_WRAPPER_PADDING_NO_BOTTOM))
    if footer:
        console.print(f"  {footer}", style=colors.muted)

    _last_output = "panel"


def display_confirmation_panel(content: str):
    """Display confirmation panel with consistent left padding."""
    global _last_output
    _prepare_to_print("panel")
    panel = create_panel(content, "Confirm Action", colors.warning)
    console.print(Padding(panel, (0, 0, 0, 1)))
    _last_output = "panel"


def display_error_panel(message: str, detail: str = None, title="Error"):
    """Display error panel with consistent padding."""
    global _last_output
    _prepare_to_print("panel")
    content = f"{message}\n\n{detail}" if detail else message
    panel = create_panel(content, title, colors.error)
    console.print(Padding(panel, PANEL_WRAPPER_PADDING))
    _last_output = "panel"


def display_info_panel(content, title: str):
    global _last_output
    _prepare_to_print("panel")
    panel = create_panel(content, title, colors.muted)
    console.print(Padding(panel, PANEL_WRAPPER_PADDING_NO_BOTTOM))
    _last_output = "panel"


def display_thinking_panel(content: str):
    global _last_output
    _prepare_to_print("panel")
    text_content = Text(content, style=colors.muted)
    panel = create_panel(text_content, "Thinking", colors.muted)
    console.print(Padding(panel, PANEL_WRAPPER_PADDING))
    _last_output = "panel"


def reset_output_context():
    """Reset the output context (used after user input)."""
    global _last_output
    _last_output = "user_input"
