"""UI Manager for centralized output control and spacing logic."""

from enum import Enum, auto
from typing import Optional, Union

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from rich.text import Text

from sidekick.ui.colors import colors
from sidekick.ui.formatting import create_syntax_highlighted


class OutputType(Enum):
    """Types of output that affect spacing decisions."""

    STATUS = auto()  # Info, error, warning messages
    PANEL = auto()  # Boxed content panels
    USER_INPUT = auto()  # After user input
    THINKING = auto()  # Thinking messages (special status)
    SPINNER = auto()  # While spinner is active


class PanelType(Enum):
    """Types of panels with different styling."""

    DEFAULT = auto()
    AGENT = auto()
    TOOL = auto()
    ERROR = auto()
    WARNING = auto()
    INFO = auto()
    CONFIRMATION = auto()
    THINKING = auto()


class MessageType(Enum):
    """Types of status messages."""

    INFO = auto()
    ERROR = auto()
    WARNING = auto()
    SUCCESS = auto()
    BULLET = auto()
    MUTED = auto()
    THINKING = auto()


# Style configuration for different panel types
PANEL_STYLES = {
    PanelType.DEFAULT: {"border_style": colors.muted, "title_prefix": ""},
    PanelType.AGENT: {"border_style": colors.primary, "title_prefix": "Sidekick"},
    PanelType.TOOL: {"border_style": colors.tool_data, "title_prefix": ""},
    PanelType.ERROR: {"border_style": colors.error, "title_prefix": "Error"},
    PanelType.WARNING: {"border_style": colors.warning, "title_prefix": "Warning"},
    PanelType.INFO: {"border_style": colors.muted, "title_prefix": ""},
    PanelType.CONFIRMATION: {"border_style": colors.warning, "title_prefix": "Confirm Action"},
    PanelType.THINKING: {"border_style": colors.muted, "title_prefix": "Thinking"},
}

# Style configuration for different message types
MESSAGE_STYLES = {
    MessageType.INFO: {"prefix": "•", "style": colors.primary},
    MessageType.ERROR: {"prefix": "✗", "style": colors.error},
    MessageType.WARNING: {"prefix": "⚠", "style": colors.warning},
    MessageType.SUCCESS: {"prefix": "✓", "style": colors.success},
    MessageType.BULLET: {"prefix": "  -", "style": colors.muted},
    MessageType.MUTED: {"prefix": "ℹ", "style": colors.muted},
    MessageType.THINKING: {"prefix": "›", "style": colors.muted},
}


class UIManager:
    """Manages UI output with automatic spacing and consistent styling."""

    PANEL_CONTENT_PADDING = 1
    PANEL_WRAPPER_PADDING = (0, 0, 0, 1)

    def __init__(self):
        self.console = Console()
        self._last_output: Optional[OutputType] = None
        self._spinner_active = False

    def _prepare_spacing(self, new_type: OutputType):
        """Add spacing based on output transitions.

        Rules:
        - Panel -> Status: add blank line
        - Any -> Panel: add blank line (except after user input)
        - Status -> Status: no spacing
        """
        if self._last_output is None:
            return

        if new_type == OutputType.STATUS and self._last_output == OutputType.PANEL:
            self.console.print()
        elif new_type == OutputType.PANEL and self._last_output != OutputType.USER_INPUT:
            self.console.print()

    def _prepare_panel_content(self, content, markdown, syntax):
        """Prepare content for display in panel.

        Args:
            content: Raw content to display
            markdown: Whether to render as markdown
            syntax: Language for syntax highlighting

        Returns:
            Formatted content ready for panel display
        """
        if markdown and isinstance(content, str):
            return Markdown(content)
        elif syntax and isinstance(content, str):
            return create_syntax_highlighted(content, syntax)
        return content

    def _determine_panel_title(self, title, panel_type, config):
        """Determine final panel title based on type and configuration.

        Args:
            title: Optional title override
            panel_type: Type of panel for special handling
            config: Panel style configuration

        Returns:
            Final title string or None
        """
        if title is None and config["title_prefix"]:
            return config["title_prefix"]
        elif title and config["title_prefix"] and panel_type == PanelType.AGENT:
            return title
        elif title and config["title_prefix"]:
            return f"{config['title_prefix']}: {title}"
        return title

    def panel(
        self,
        content: Union[str, Text],
        *,
        title: Optional[str] = None,
        panel_type: PanelType = PanelType.DEFAULT,
        footer: Optional[str] = None,
        markdown: bool = False,
        syntax: Optional[str] = None,
        has_footer: bool = False,
    ):
        """Display a panel with automatic spacing and styling.

        Args:
            content: Content to display in the panel
            title: Optional title override
            panel_type: Type of panel for styling
            footer: Optional footer text (displayed below panel)
            markdown: Whether to render content as markdown
            syntax: Language for syntax highlighting (alternative to markdown)
            has_footer: Whether external footer will be shown (affects padding)
        """
        self._prepare_spacing(OutputType.PANEL)

        config = PANEL_STYLES[panel_type]
        display_content = self._prepare_panel_content(content, markdown, syntax)
        final_title = self._determine_panel_title(title, panel_type, config)

        panel = Panel(
            Padding(display_content, self.PANEL_CONTENT_PADDING),
            title=final_title,
            title_align="left",
            border_style=config["border_style"],
        )

        self.console.print(Padding(panel, self.PANEL_WRAPPER_PADDING))

        if footer:
            self.console.print(f"  {footer}", style=colors.muted)

        self._last_output = OutputType.PANEL

    def message(
        self,
        text: str,
        *,
        message_type: MessageType = MessageType.INFO,
        indent: int = 0,
        detail: Optional[str] = None,
    ):
        """Display a status message with automatic spacing.

        Args:
            text: Message text
            message_type: Type of message for styling
            indent: Additional spaces to indent
            detail: Optional detail text (for errors)
        """
        self._prepare_spacing(OutputType.STATUS)

        config = MESSAGE_STYLES[message_type]
        prefix = config["prefix"]
        style = config["style"]

        if message_type == MessageType.THINKING:
            lines = text.strip().split("\n")
            if lines:
                self.console.print(f"{prefix} {lines[0]}", style=style)
                for line in lines[1:]:
                    self.console.print(f"  {line}", style=style)
        else:
            indent_str = " " * indent
            if prefix:
                msg = f"{indent_str}{prefix} {text}"
            else:
                msg = f"{indent_str}{text}"

            if detail and message_type == MessageType.ERROR:
                msg = f"{msg}: {detail}"

            self.console.print(msg, style=style)

        self._last_output = OutputType.STATUS

    def line(self):
        """Print a blank line without affecting output context."""
        self.console.print()

    def reset_context(self):
        """Reset output context (typically after user input)."""
        self._last_output = OutputType.USER_INPUT

    def set_spinner_active(self, active: bool):
        """Update spinner state and preserve spacing context.

        Args:
            active: Whether spinner is active
        """
        self._spinner_active = active
        if active and self._last_output not in (OutputType.PANEL, OutputType.USER_INPUT):
            self._last_output = OutputType.SPINNER

    def agent(self, content: str, has_footer: bool = False):
        """Display agent response panel."""
        self.panel(
            content,
            title="Sidekick",
            panel_type=PanelType.AGENT,
            markdown=True,
            has_footer=has_footer,
        )

    def tool(self, content: Union[str, Text], title: str, footer: Optional[str] = None):
        """Display tool output panel."""
        self.panel(
            content,
            title=title,
            panel_type=PanelType.TOOL,
            footer=footer,
        )

    def error_panel(self, message: str, detail: Optional[str] = None, title: Optional[str] = None):
        """Display error panel."""
        content = f"{message}\n\n{detail}" if detail else message
        self.panel(
            content,
            title=title,
            panel_type=PanelType.ERROR,
        )

    def info(self, text: str):
        """Display info message."""
        self.message(text, message_type=MessageType.INFO)

    def error(self, text: str, detail: Optional[str] = None):
        """Display error message."""
        self.message(text, message_type=MessageType.ERROR, detail=detail)

    def warning(self, text: str):
        """Display warning message."""
        self.message(text, message_type=MessageType.WARNING)

    def success(self, text: str):
        """Display success message."""
        self.message(text, message_type=MessageType.SUCCESS)

    def bullet(self, text: str):
        """Display bullet point."""
        self.message(text, message_type=MessageType.BULLET)

    def muted(self, text: str, indent: int = 0):
        """Display muted text."""
        self.message(text, message_type=MessageType.MUTED, indent=indent)

    def thinking(self, text: str):
        """Display thinking message."""
        self.message(text, message_type=MessageType.THINKING)

    def thinking_panel(self, content: str):
        """Display thinking panel."""
        self.panel(content, panel_type=PanelType.THINKING)

    def confirmation_panel(self, content: str):
        """Display confirmation panel."""
        self.panel(content, panel_type=PanelType.CONFIRMATION)

    def info_panel(self, content, title: str):
        """Display info panel."""
        self.panel(content, title=title, panel_type=PanelType.INFO)

    def dump(self, data):
        """Display data in a pretty format.

        Args:
            data: Any data structure to display
        """
        self.console.print(Pretty(data))

    def help(self):
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

        self.panel(table, title="Available Commands", panel_type=PanelType.INFO)
