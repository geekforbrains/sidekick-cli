"""Syntax highlighting utilities for displaying code with proper formatting."""

import difflib
from pathlib import Path

from rich.syntax import Syntax
from rich.text import Text


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


def create_syntax_highlighted(content: str, filepath: str, theme: str = "monokai") -> Syntax:
    """Create a syntax-highlighted Rich Syntax object.

    Args:
        content: The code content to highlight
        filepath: Path to the file (used for language detection)
        theme: Pygments theme name (default: "monokai")

    Returns:
        Rich Syntax object ready for display
    """
    language = get_file_language(filepath)

    return Syntax(
        content,
        language,
        theme=theme,
        line_numbers=True,
        word_wrap=False,
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
