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
from sidekick.utils.display import format_tool_name

console = Console()

# Padding constants for consistent spacing
PANEL_CONTENT_PADDING = 1
PANEL_WRAPPER_PADDING = (0, 0, 0, 1)
PANEL_WRAPPER_PADDING_NO_BOTTOM = (1, 0, 0, 1)
PANEL_WRAPPER_PADDING_NO_TOP = (0, 0, 1, 1)
PANEL_WRAPPER_PADDING_AGENT = (0, 0, 0, 1)

SYNTAX_THEME = "monokai"


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


def display_panel(panel, bottom_padding: bool = True):
    """Display a panel with consistent wrapper padding.

    Args:
        panel: The panel to display
        bottom_padding: Whether to include bottom padding (default: True)
    """
    padding = PANEL_WRAPPER_PADDING if bottom_padding else PANEL_WRAPPER_PADDING_NO_BOTTOM
    console.print(Padding(panel, padding))


def display_agent_panel(content: str):
    """Display agent response panel with specific padding."""
    panel = create_panel(Markdown(content), "Sidekick", colors.primary)
    console.print(Padding(panel, PANEL_WRAPPER_PADDING))


def display_tool_panel(content, title: str, footer: str = None):
    """Display tool data panel with optional footer."""
    panel = create_panel(content, title, colors.tool_data)

    if footer:
        console.print(Padding(panel, PANEL_WRAPPER_PADDING_NO_BOTTOM))
        console.print(f"  {footer}", style=colors.muted)
        console.print()
    else:
        console.print(Padding(panel, PANEL_WRAPPER_PADDING))


def display_confirmation_panel(content: str):
    """Display confirmation panel with consistent left padding."""
    panel = create_panel(content, "Confirm Action", colors.warning)
    console.print(Padding(panel, (0, 0, 0, 1)))


def display_error_panel(message: str, detail: str = None):
    """Display error panel with consistent padding."""
    content = f"{message}\n\n{detail}" if detail else message
    panel = create_panel(content, "Error", colors.error)
    display_panel(panel)


def display_info_panel(content, title: str):
    """Display info panel with consistent padding."""
    panel = create_panel(content, title, colors.muted)
    display_panel(panel)


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
    display_error_panel(message, detail)


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
    display_agent_panel(content)


def line():
    """Print a simple line separator."""
    console.print()


def dump(data):
    """Display data in a formatted panel."""
    pretty = Pretty(data, expand_all=True)
    display_info_panel(pretty, "Message History")


def _display_write_file_confirmation(args: dict):
    """Display confirmation for write_file tool."""
    syntax = create_syntax_highlighted(args["content"], args["filepath"])
    panel = create_panel(syntax, "Write File", colors.warning)
    display_panel(panel, bottom_padding=False)
    console.print(f"  File: {args['filepath']}", style=colors.muted)
    console.print()


def _display_update_file_confirmation(args: dict):
    """Display confirmation for update_file tool with diff."""
    filepath = args["filepath"]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            current_content = f.read()

        updated_content = current_content.replace(args["old_content"], args["new_content"], 1)

        diff_text = create_unified_diff(current_content, updated_content, filepath)
        panel = create_panel(diff_text, f"Update File: {filepath}", colors.warning)
        display_panel(panel, bottom_padding=False)
    except Exception as e:
        error_text = f"Error reading file: {str(e)}"
        panel = create_panel(error_text, f"Update File: {filepath}", colors.error)
        display_panel(panel, bottom_padding=False)

    console.print(f"  File: {filepath}", style=colors.muted)
    console.print()


def _display_git_add_confirmation(args: dict):
    """Display confirmation for git_add tool."""
    import subprocess

    try:
        # Get current git status
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )

        if not result.stdout.strip():
            content = "No changes to stage"
        else:
            # Parse status and group by type
            files_to_stage = []
            for line in result.stdout.splitlines():
                if line:
                    status = line[:2]
                    filepath = line[3:]

                    # Determine what will be staged based on the files argument
                    if args["files"] == "." or args["files"] in filepath:
                        if status[1] == "M":
                            files_to_stage.append(f"[orange1]modified:[/orange1]   {filepath}")
                        elif status[1] == "?":
                            files_to_stage.append(f"[green]new file:[/green]   {filepath}")
                        elif status[1] == "D":
                            files_to_stage.append(f"[red]deleted:[/red]    {filepath}")
                        elif status[0] == " " and status[1] != " ":
                            files_to_stage.append(f"[orange1]modified:[/orange1]   {filepath}")

            if files_to_stage:
                content = "Files to be staged:\n\n" + "\n".join(files_to_stage)
            else:
                content = "No matching files to stage"

    except Exception as e:
        content = f"Error getting git status: {str(e)}"

    panel = create_panel(content, f"Git Add: {args['files']}", colors.warning)
    display_panel(panel, bottom_padding=False)
    console.print()


def _display_git_commit_confirmation(args: dict):
    """Display confirmation for git_commit tool."""
    import subprocess

    try:
        # Get staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-status"], capture_output=True, text=True, check=True
        )

        if not result.stdout.strip():
            staged_info = "No staged changes"
        else:
            # Parse staged files
            staged_files = []
            for line in result.stdout.splitlines():
                if line:
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        status, filepath = parts
                        if status == "M":
                            staged_files.append(f"[orange1]modified:[/orange1]   {filepath}")
                        elif status == "A":
                            staged_files.append(f"[green]new file:[/green]   {filepath}")
                        elif status == "D":
                            staged_files.append(f"[red]deleted:[/red]    {filepath}")

            # Get diff stats
            stats_result = subprocess.run(
                ["git", "diff", "--cached", "--stat"], capture_output=True, text=True, check=True
            )

            stats_line = ""
            if stats_result.stdout:
                lines = stats_result.stdout.strip().split("\n")
                if lines:
                    stats_line = lines[-1]  # Last line contains the summary

            staged_info = "Staged changes:\n\n" + "\n".join(staged_files)
            if stats_line:
                staged_info += f"\n\n[dim]{stats_line}[/dim]"

        # Format commit message
        message = args["message"]
        content = f"{staged_info}\n\n[bold]Commit message:[/bold]\n{message}"

    except Exception as e:
        content = f"Error getting staged changes: {str(e)}"

    panel = create_panel(content, "Git Commit", colors.warning)
    display_panel(panel, bottom_padding=False)
    console.print()


def _display_generic_tool_confirmation(tool_name: str, args: dict, formatted_name: str):
    """Display generic tool confirmation."""
    content_lines = [f"Tool: [bold]{formatted_name}[/bold]", ""]

    for key, value in args.items():
        if isinstance(value, str):
            value = value.strip()
            if len(value) > 100:
                value = value[:97] + "..."
        content_lines.append(f"• {key}: {value}")

    # Generate always text based on tool type
    always_text = _get_always_text(tool_name, args)

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

    # Show file path for file-related tools
    if tool_name == "update_file" and "filepath" in args:
        console.print(f"  File: {args['filepath']}", style=colors.muted)
        console.print()


def _display_search_files_confirmation(args: dict):
    """Display confirmation for search_files tool."""
    pattern = args["pattern"]
    content = f"Searching for files matching pattern: [bold]{pattern}[/bold]"
    panel = create_panel(content, f"Search Files: {pattern}", colors.warning)
    display_panel(panel, bottom_padding=False)
    console.print()


def _display_search_content_confirmation(args: dict):
    """Display confirmation for search_content tool."""
    text_pattern = args["text_pattern"]
    content = f"Searching for content matching pattern: [bold]{text_pattern}[/bold]"
    panel = create_panel(content, f"Search Content: {text_pattern}", colors.warning)
    display_panel(panel, bottom_padding=False)
    console.print()


def _display_search_dirs_confirmation(args: dict):
    """Display confirmation for search_dirs tool."""
    pattern = args["pattern"]
    content = f"Searching for directories matching pattern: [bold]{pattern}[/bold]"
    panel = create_panel(content, f"Search Directories: {pattern}", colors.warning)
    display_panel(panel, bottom_padding=False)
    console.print()


def _get_always_text(tool_name: str, args: dict) -> str:
    """Generate the 'always allow' text based on tool type."""
    if tool_name == "run_command" and "command" in args:
        from sidekick.utils.command_parser import extract_commands

        commands = extract_commands(args["command"])
        if len(commands) > 1:
            return f"  a - Always allow: {', '.join(commands)}"
        else:
            return (
                f"  a - Always allow '{commands[0]}' commands"
                if commands
                else "  a - Always allow this command"
            )
    else:
        return "  a - Always allow this tool"


async def confirm_tool_call(tool_name: str, args: dict) -> str:
    """
    Prompt user for confirmation before executing a tool.

    Returns:
        'yes' - Execute this tool
        'always' - Execute this tool and don't ask again for this tool type
        'no' - Cancel this tool execution
    """
    formatted_name = format_tool_name(tool_name)

    # Display tool-specific confirmation
    if tool_name == "write_file" and "content" in args and "filepath" in args:
        _display_write_file_confirmation(args)
    elif tool_name == "update_file" and all(
        k in args for k in ["filepath", "old_content", "new_content"]
    ):
        _display_update_file_confirmation(args)
    elif tool_name == "git_add" and "files" in args:
        _display_git_add_confirmation(args)
    elif tool_name == "git_commit" and "message" in args:
        _display_git_commit_confirmation(args)
    elif tool_name == "search_files" and "pattern" in args:
        _display_search_files_confirmation(args)
    elif tool_name == "search_content" and "text_pattern" in args:
        _display_search_content_confirmation(args)
    elif tool_name == "search_dirs" and "pattern" in args:
        _display_search_dirs_confirmation(args)
    else:
        _display_generic_tool_confirmation(tool_name, args, formatted_name)

    # Get user choice
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
