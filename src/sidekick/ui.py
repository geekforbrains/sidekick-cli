import asyncio
import difflib
import random
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.pretty import Pretty
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from sidekick.constants import APP_NAME, APP_VERSION
from sidekick.session import session

console = Console()

# Padding constants for consistent spacing
PANEL_CONTENT_PADDING = 1
PANEL_WRAPPER_PADDING = (0, 0, 0, 1)  # Standard panel padding (left indent)
PANEL_WRAPPER_PADDING_NO_BOTTOM = (0, 0, 0, 1)  # Used for panels with footers

SYNTAX_THEME = "monokai"

# Track last output type for consistent spacing
_last_output = None  # "status", "panel", "user_input", or None


# Color scheme from main branch
class Colors:
    primary = "medium_purple1"  # Agent responses
    secondary = "medium_purple3"  # Secondary purple
    success = "green"  # Success messages
    warning = "orange1"  # Confirmations/warnings
    error = "red"  # Errors
    muted = "grey62"  # Info/help
    tool_data = "bright_blue"  # Tool output data


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


def display_agent_panel(content: str):
    """Display agent response panel with specific padding."""
    global _last_output

    # Add space before panel if needed
    if _last_output == "status":
        console.print()
    elif _last_output == "panel":
        console.print()

    panel = create_panel(Markdown(content), "Sidekick", colors.primary)
    console.print(Padding(panel, PANEL_WRAPPER_PADDING))
    # Don't add space here - let caller handle it (for usage footer)

    _last_output = "panel"


def display_tool_panel(content, title: str, footer: str = None):
    """Display tool data panel with optional footer."""
    global _last_output

    # Add space before panel if needed
    if _last_output == "status":
        console.print()
    elif _last_output == "panel":
        console.print()

    panel = create_panel(content, title, colors.tool_data)

    if footer:
        console.print(Padding(panel, PANEL_WRAPPER_PADDING_NO_BOTTOM))
        console.print(f"  {footer}", style=colors.muted)
        console.print()  # Space after footer
    else:
        console.print(Padding(panel, PANEL_WRAPPER_PADDING))
        console.print()  # Space after panel

    _last_output = "panel"


def display_confirmation_panel(content: str):
    """Display confirmation panel with consistent left padding."""
    global _last_output

    # Add space before panel if needed
    if _last_output == "status":
        console.print()
    elif _last_output == "panel":
        console.print()

    panel = create_panel(content, "Confirm Action", colors.warning)
    console.print(Padding(panel, (0, 0, 0, 1)))
    # No space after - expecting user input

    _last_output = "panel"


def display_error_panel(message: str, detail: str = None):
    """Display error panel with consistent padding."""
    global _last_output

    # Add space before panel if needed
    if _last_output == "status":
        console.print()
    elif _last_output == "panel":
        console.print()

    content = f"{message}\n\n{detail}" if detail else message
    panel = create_panel(content, "Error", colors.error)
    console.print(Padding(panel, PANEL_WRAPPER_PADDING))
    console.print()  # Space after panel

    _last_output = "panel"


def display_info_panel(content, title: str):
    """Display info panel with consistent padding."""
    global _last_output

    # Add space before panel if needed
    if _last_output == "status":
        console.print()
    elif _last_output == "panel":
        console.print()

    panel = create_panel(content, title, colors.muted)
    console.print(Padding(panel, PANEL_WRAPPER_PADDING))
    console.print()  # Space after panel

    _last_output = "panel"


# Style definitions
class SpinnerStyle:
    DEFAULT = f"[bold {colors.primary}]{{}}[/bold {colors.primary}]"
    MUTED = f"[{colors.muted}]{{}}[/{colors.muted}]"
    WARNING = f"[{colors.warning}]{{}}[/{colors.warning}]"
    ERROR = f"[{colors.error}]{{}}[/{colors.error}]"


def banner():
    """Display the application banner."""
    global _last_output
    console.clear()
    banner_padding = Padding(BANNER, (1, 0, 0, 2))
    version_padding = Padding(f"v{APP_VERSION}", (0, 0, 1, 2))
    console.print(banner_padding, style=colors.primary)
    console.print(version_padding, style=colors.muted)
    _last_output = None  # Reset context after banner


def info(message: str):
    """Display an info message."""
    global _last_output

    # Add space before status if coming from panel
    if _last_output == "panel":
        console.print()

    console.print(f"• {message}", style=colors.primary)
    _last_output = "status"


def error(message: str, detail: str = None):
    """Display an error message with optional detail.

    Args:
        message: The main error message
        detail: Optional detailed error information
    """
    display_error_panel(message, detail)


def warning(message: str):
    """Display a warning message."""
    global _last_output

    # Add space before status if coming from panel
    if _last_output == "panel":
        console.print()

    console.print(f"• {message}", style=colors.warning)
    _last_output = "status"


def success(message: str):
    """Display a success message."""
    global _last_output

    # Add space before status if coming from panel
    if _last_output == "panel":
        console.print()

    console.print(f"• {message}", style=colors.success)
    _last_output = "status"


def bullet(message: str):
    """Display a bulleted list item."""
    global _last_output

    # Add space before status if coming from panel
    if _last_output == "panel":
        console.print()

    console.print(f"  • {message}", style=colors.muted)
    _last_output = "status"


def muted(message: str, spaces: int = 0):
    """Display a muted message."""
    global _last_output

    # Add space before status if coming from panel
    if _last_output == "panel":
        console.print()

    console.print(f"{' ' * spaces}• {message}", style=colors.muted)
    _last_output = "status"


def agent(content: str, has_footer: bool = False):
    """Display agent output with markdown formatting.
    
    Args:
        content: The markdown content to display
        has_footer: If True, don't add space after (footer will handle it)
    """
    display_agent_panel(content)
    if not has_footer:
        console.print()  # Add space if no footer coming


def line():
    """Print a simple line separator."""
    global _last_output
    console.print()
    # Don't update _last_output - line() is explicit spacing


def reset_output_context():
    """Reset the output context after user input."""
    global _last_output
    _last_output = "user_input"


def dump(data):
    """Display data in a formatted panel."""
    pretty = Pretty(data, expand_all=True)
    display_info_panel(pretty, "Message History")


def start_spinner(message: str, style: str = SpinnerStyle.DEFAULT):
    """Start a spinner and store it in session."""
    formatted_message = style.format(message)
    session.spinner = console.status(formatted_message, spinner="star2")
    session.spinner.start()

    if session.spinner_rotation_task:
        session.spinner_rotation_task.cancel()

    try:
        loop = asyncio.get_running_loop()
        session.spinner_rotation_task = loop.create_task(_rotate_thinking_messages(style))
    except RuntimeError:
        pass


def stop_spinner():
    """Stop and clear the session spinner."""
    if session.spinner_rotation_task:
        session.spinner_rotation_task.cancel()
        session.spinner_rotation_task = None

    if session.spinner:
        session.spinner.stop()
        session.spinner = None


def help():
    """Display the available commands."""
    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    table.add_column("Command", style=colors.primary, justify="right")
    table.add_column("Description", style="white")

    commands = [
        ("/help", "Show this help message"),
        ("/clear", "Clear the conversation history"),
        ("/yolo", "Toggle confirmation prompts on/off"),
        ("/model", "List available models"),
        ("/model <n>", "Switch to a specific model"),
        ("/model <n> default", "Set a model as the default"),
        ("/usage", "Show session usage statistics"),
        ("exit", "Exit the application"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    display_info_panel(table, "Available Commands")


def version():
    """Display version information."""
    console.print(f"• {APP_NAME} v{APP_VERSION}", style=colors.primary)


def update_available(latest_version: str):
    """Display update available message."""
    warning(f"Update available: v{latest_version}")
    muted("Exit, and run: [bold]pip install --upgrade sidekick-cli[/bold]", spaces=2)


def usage(usage_data: dict):
    """Display usage information in the compact format."""
    global _last_output

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

    # Use two spaces to align with panel content
    console.print(f"  {msg}", style=colors.muted)
    # Don't add space - let the main loop handle spacing before prompt
    # Keep _last_output as "panel" since this is a footer


def get_file_language(filepath: str) -> str:
    """Detect programming language from file extension.

    Args:
        filepath: Path to the file

    Returns:
        Language identifier for Rich syntax highlighting
    """
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".lua": "lua",
        ".dart": "dart",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".fish": "fish",
        ".ps1": "powershell",
        ".sql": "sql",
        ".html": "html",
        ".htm": "html",
        ".xml": "xml",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".conf": "ini",
        ".md": "markdown",
        ".rst": "rst",
        ".tex": "latex",
        ".dockerfile": "dockerfile",
        ".makefile": "makefile",
        ".cmake": "cmake",
        ".vim": "vim",
        ".el": "elisp",
        ".clj": "clojure",
        ".ex": "elixir",
        ".exs": "elixir",
        ".erl": "erlang",
        ".hrl": "erlang",
        ".hs": "haskell",
        ".ml": "ocaml",
        ".mli": "ocaml",
        ".fs": "fsharp",
        ".fsx": "fsharp",
        ".pl": "perl",
        ".pm": "perl",
        ".jl": "julia",
        ".nim": "nim",
        ".nix": "nix",
        ".vue": "vue",
        ".svelte": "svelte",
    }

    # Get file extension
    path = Path(filepath)
    ext = path.suffix.lower()

    # Check for special filenames
    filename = path.name.lower()
    if filename == "dockerfile":
        return "dockerfile"
    elif filename == "makefile":
        return "makefile"
    elif filename == "cmakelists.txt":
        return "cmake"

    # Return mapped language or default to text
    return extension_map.get(ext, "text")


def create_syntax_highlighted(content: str, filepath: str, theme: str = None) -> Syntax:
    """Create a syntax-highlighted Rich Syntax object.

    Args:
        content: The code content to highlight
        filepath: Path to the file (used for language detection)
        theme: Pygments theme name (default: from SYNTAX_THEME)

    Returns:
        Rich Syntax object ready for display
    """
    if theme is None:
        theme = SYNTAX_THEME

    language = get_file_language(filepath)

    return Syntax(
        content,
        language,
        theme=theme,
        line_numbers=True,
        word_wrap=False,
    )


def create_shell_syntax(command: str, theme: str = None) -> Syntax:
    """Create a syntax-highlighted shell command.

    Args:
        command: The shell command to highlight
        theme: Pygments theme name (default: from SYNTAX_THEME)

    Returns:
        Rich Syntax object ready for display
    """
    if theme is None:
        theme = SYNTAX_THEME

    return Syntax(
        command,
        "bash",
        theme=theme,
        line_numbers=False,
        word_wrap=True,
    )


def create_unified_diff(
    old_content: str, new_content: str, filepath: str, context_lines: int = 3
) -> Text:
    """Create a unified diff with syntax highlighting.

    Args:
        old_content: The original content
        new_content: The new content
        filepath: Path to the file (used for header)
        context_lines: Number of context lines to show (default: 3)

    Returns:
        Rich Text object with colored diff
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            old_lines, new_lines, fromfile=filepath, tofile=filepath, n=context_lines
        )
    )

    if not diff_lines:
        return Text("No changes detected", style="dim")

    diff_text = Text()

    for line in diff_lines:
        if line.startswith("+++") or line.startswith("---"):
            diff_text.append(line, style="bold blue")
        elif line.startswith("@@"):
            diff_text.append(line, style="cyan")
        elif line.startswith("+"):
            diff_text.append(line, style="green")
        elif line.startswith("-"):
            diff_text.append(line, style="red")
        else:
            diff_text.append(line)

    return diff_text


def create_inline_diff(old_content: str, new_content: str) -> tuple[Text, Text]:
    """Create inline diff showing old and new content side by side.

    Args:
        old_content: The original content
        new_content: The new content

    Returns:
        Tuple of (old_text, new_text) with highlighting
    """
    old_text = Text(old_content)
    new_text = Text(new_content)

    old_text.stylize("red")
    new_text.stylize("green")

    return old_text, new_text
