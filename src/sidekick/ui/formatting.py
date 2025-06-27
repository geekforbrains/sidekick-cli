"""Formatting functions for syntax highlighting, diffs, and display."""

import difflib
from pathlib import Path

from rich.syntax import Syntax
from rich.text import Text

SYNTAX_THEME = "monokai"


def get_file_language(filepath: str) -> str:
    """Determine the language for syntax highlighting based on file extension.

    Args:
        filepath: Path to the file

    Returns:
        Language identifier for rich.syntax.Syntax
    """
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".json": "json",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".conf": "ini",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".fish": "fish",
        ".ps1": "powershell",
        ".bat": "batch",
        ".cmd": "batch",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".swift": "swift",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".cc": "cpp",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".lua": "lua",
        ".pl": "perl",
        ".r": "r",
        ".R": "r",
        ".m": "matlab",
        ".jl": "julia",
        ".scala": "scala",
        ".clj": "clojure",
        ".elm": "elm",
        ".ex": "elixir",
        ".exs": "elixir",
        ".erl": "erlang",
        ".hrl": "erlang",
        ".vim": "vim",
        ".vimrc": "vim",
        ".sql": "sql",
        ".dockerfile": "docker",
        ".Dockerfile": "docker",
        ".md": "markdown",
        ".markdown": "markdown",
        ".rst": "rst",
        ".tex": "latex",
        ".vue": "vue",
        ".svelte": "svelte",
    }

    # Get the file extension
    ext = Path(filepath).suffix.lower()

    # Check if we have a mapping for this extension
    if ext in ext_map:
        return ext_map[ext]

    # Check for some special filenames
    filename = Path(filepath).name.lower()
    if filename == "dockerfile":
        return "docker"
    elif filename == "makefile":
        return "makefile"
    elif filename == ".gitignore":
        return "gitignore"
    elif filename == ".env":
        return "dotenv"

    # Default to text if we don't recognize the extension
    return "text"


def create_syntax_highlighted(content: str, filepath: str, theme: str = None) -> Syntax:
    """Create syntax-highlighted content.

    Args:
        content: The content to highlight
        filepath: Path to determine language
        theme: Optional theme override

    Returns:
        Syntax object for rendering
    """
    if theme is None:
        theme = SYNTAX_THEME

    language = get_file_language(filepath)
    return Syntax(
        content,
        language,
        theme=theme,
        line_numbers=True,
        word_wrap=True,
    )


def create_shell_syntax(command: str, theme: str = None) -> Syntax:
    """Create syntax-highlighted shell command.

    Args:
        command: Shell command to highlight
        theme: Optional theme override

    Returns:
        Syntax object for rendering
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
    old_content: str, new_content: str, filepath: str = "file", context_lines: int = 3
) -> Syntax:
    """Create a unified diff with syntax highlighting.

    Args:
        old_content: Original file content
        new_content: Modified file content
        filepath: Path for diff header
        context_lines: Number of context lines

    Returns:
        Syntax object with highlighted diff
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        n=context_lines,
        lineterm="",
    )

    diff_text = "".join(diff)

    return Syntax(
        diff_text,
        "diff",
        theme=SYNTAX_THEME,
        line_numbers=False,
        word_wrap=True,
    )


def create_inline_diff(old_content: str, new_content: str) -> tuple[Text, Text]:
    """Create inline diffs showing character-level changes.

    Args:
        old_content: Original content
        new_content: New content

    Returns:
        Tuple of (old_text, new_text) with highlighting
    """
    old_text = Text()
    new_text = Text()

    # Use difflib to find character-level differences
    matcher = difflib.SequenceMatcher(None, old_content, new_content)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            old_text.append(old_content[i1:i2])
            new_text.append(new_content[j1:j2])
        elif tag == "delete":
            old_text.append(old_content[i1:i2], style="red strike")
        elif tag == "insert":
            new_text.append(new_content[j1:j2], style="green")
        elif tag == "replace":
            old_text.append(old_content[i1:i2], style="red strike")
            new_text.append(new_content[j1:j2], style="green")

    return old_text, new_text


def format_server_name(key: str) -> str:
    """Convert server key to human-readable name.

    Args:
        key: Server key (e.g., 'npmScripts')

    Returns:
        Human-readable name (e.g., 'NPM Scripts')
    """
    # Handle camelCase
    result = ""
    for i, char in enumerate(key):
        if i > 0 and char.isupper() and key[i - 1].islower():
            result += " "
        result += char

    # Handle snake_case and hyphenated names
    result = result.replace("_", " ").replace("-", " ")

    # Capitalize words, but preserve certain acronyms
    words = result.split()
    formatted_words = []
    acronyms = {"npm", "mcp", "api", "cli", "url", "uri", "id", "ui"}

    for word in words:
        if word.lower() in acronyms:
            formatted_words.append(word.upper())
        else:
            formatted_words.append(word.capitalize())

    return " ".join(formatted_words)


def get_command_display_name(command_string: str) -> str:
    """Get a display-friendly version of the commands for UI.

    Args:
        command_string: The full shell command string

    Returns:
        A comma-separated list of command names
    """
    # Import here to avoid circular dependency
    from sidekick.utils.command import extract_commands

    commands = extract_commands(command_string)
    if len(commands) == 1:
        return f"'{commands[0]}'"
    else:
        return ", ".join(f"'{cmd}'" for cmd in commands)
