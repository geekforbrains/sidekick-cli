import asyncio
import fnmatch
import os
import re
import shutil
from pathlib import Path
from typing import Optional, Set

from pydantic_ai import RunContext

from sidekick.deps import ToolDeps

EXCLUDE_DIRS = {
    # Version control
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    # Dependencies
    "node_modules",
    "bower_components",
    "vendor",
    "packages",
    # Python
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "venv",
    ".venv",
    "env",
    ".env",
    "virtualenv",
    "*.egg-info",
    ".eggs",
    ".tox",
    "pip-wheel-metadata",
    # Build outputs
    "build",
    "dist",
    "out",
    "target",
    "bin",
    "obj",
    "_build",
    "_site",
    ".build",
    # IDE/Editor
    ".idea",
    ".vscode",
    ".vs",
    "*.swp",
    "*.swo",
    "*~",
    ".project",
    ".classpath",
    ".settings",
    # Testing/Coverage
    ".coverage",
    "htmlcov",
    "coverage",
    ".nyc_output",
    "test-results",
    "test-reports",
    # Web/JS
    ".next",
    ".nuxt",
    ".cache",
    ".parcel-cache",
    ".turbo",
    ".webpack",
    ".rollup.cache",
    ".fusebox",
    ".dynamodb",
    # Temporary
    "tmp",
    "temp",
    ".tmp",
    ".temp",
    "logs",
    "*.log",
    # OS
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    # Other
    ".sass-cache",
    ".terraform",
    ".serverless",
}

BINARY_EXTENSIONS = {
    # Images
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".webp",
    # Documents
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    # Archives
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".jar",
    ".war",
    ".ear",
    # Media
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".wav",
    ".flac",
    ".mkv",
    # Executables
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".app",
    # Data
    ".db",
    ".sqlite",
    ".sqlite3",
    ".dat",
    ".bin",
    # Other
    ".pyc",
    ".pyo",
    ".class",
    ".o",
    ".a",
    ".lib",
}


def _get_gitignore_patterns() -> Set[str]:
    """Read .gitignore patterns if it exists."""
    patterns = set()
    gitignore_path = Path(".gitignore")

    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.add(line.rstrip("/"))
        except Exception:
            pass

    return patterns


async def _grep_with_ripgrep(
    pattern: str,
    case_sensitive: bool = True,
    max_count: Optional[int] = None,
    include_pattern: Optional[str] = None,
) -> Optional[str]:
    """Use ripgrep (fastest, respects .gitignore by default)."""
    if not shutil.which("rg"):
        return None

    command = ["rg", "-n"]

    if not case_sensitive:
        command.append("-i")

    if max_count:
        command.extend(["-m", str(max_count)])

    if include_pattern:
        command.extend(["--glob", include_pattern])

    command.extend(["--", pattern, "."])

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0 or (process.returncode == 1 and not stderr.strip()):
            output = stdout.decode().strip()
            return output or "No results found."
    except Exception:
        pass

    return None


async def _grep_with_ag(
    pattern: str,
    case_sensitive: bool = True,
    max_count: Optional[int] = None,
    include_pattern: Optional[str] = None,
) -> Optional[str]:
    """Use ag (The Silver Searcher) - fast and respects .gitignore."""
    if not shutil.which("ag"):
        return None

    command = ["ag", "--numbers"]

    if not case_sensitive:
        command.append("-i")

    if max_count:
        command.extend(["-m", str(max_count)])

    if include_pattern:
        command.extend(["-G", include_pattern])

    command.extend([pattern, "."])

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0 or (process.returncode == 1 and not stderr.strip()):
            output = stdout.decode().strip()
            return output or "No results found."
    except Exception:
        pass

    return None


async def _grep_with_unix_grep(
    pattern: str,
    case_sensitive: bool = True,
    max_count: Optional[int] = None,
    include_pattern: Optional[str] = None,
) -> Optional[str]:
    """Use traditional Unix grep with smart exclusions."""
    if not shutil.which("grep"):
        return None

    command = ["grep", "-r", "-n", "-I"]

    if not case_sensitive:
        command.append("-i")

    exclude_patterns = EXCLUDE_DIRS.copy()
    exclude_patterns.update(_get_gitignore_patterns())

    for directory in exclude_patterns:
        if "*" not in directory and "/" not in directory:
            command.append(f"--exclude-dir={directory}")

    for ext in BINARY_EXTENSIONS:
        command.append(f"--exclude=*{ext}")

    if include_pattern:
        command.extend(["--include", include_pattern])

    command.extend([pattern, "."])

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0 or (process.returncode == 1 and not stderr.strip()):
            output = stdout.decode().strip()

            if output and max_count:
                lines = output.splitlines()
                if len(lines) > max_count:
                    output = "\n".join(lines[:max_count])
                    output += f"\n... (showing first {max_count} results)"

            return output or "No results found."
    except Exception:
        pass

    return None


async def _grep_with_python(
    pattern: str,
    case_sensitive: bool = True,
    max_count: Optional[int] = None,
    include_pattern: Optional[str] = None,
) -> str:
    """Pure Python fallback implementation."""
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Invalid regex pattern: {e}"

    exclude_patterns = EXCLUDE_DIRS.copy()
    exclude_patterns.update(_get_gitignore_patterns())

    results = []
    count = 0

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_patterns and not d.startswith(".")]

        skip_root = False
        for exclude in exclude_patterns:
            if exclude in root:
                skip_root = True
                break
        if skip_root:
            continue

        for file in files:
            if max_count and count >= max_count:
                results.append(f"... (showing first {max_count} results)")
                return "\n".join(results) if results else "No results found."

            if any(file.endswith(ext) for ext in BINARY_EXTENSIONS):
                continue

            if include_pattern:
                if not fnmatch.fnmatch(file, include_pattern):
                    continue

            filepath = os.path.join(root, file)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            result_line = f"{filepath}:{line_num}:{line.rstrip()}"
                            results.append(result_line)
                            count += 1

                            if max_count and count >= max_count:
                                break
            except (OSError, PermissionError):
                continue

    return "\n".join(results) if results else "No results found."


async def grep(
    ctx: RunContext[ToolDeps],
    directory: str = ".",
    pattern: str = "",
    *,
    case_sensitive: bool = True,
    max_results: Optional[int] = None,
    include_pattern: Optional[str] = None,
) -> str:  # noqa: N802
    """Search for text patterns in file contents.

    Examples:
        grep(".", "TODO")                    # Find all TODOs in current directory
        grep("src", "def main")              # Find "def main" in src/ directory
        grep(".", "error", case_sensitive=False)  # Case-insensitive search
        grep(".", "import.*pandas")          # Regex search for pandas imports
        grep(".", "TODO", max_results=10)    # Limit to first 10 results
        grep(".", "class", include_pattern="*.py")  # Search only Python files

    Args:
        directory: Directory to search in (default: current directory ".")
        pattern: Text or regex pattern to search for
            - Plain text: searches for exact text match
            - Regex: supports full regex syntax (e.g., "def\\s+\\w+\\(")
        case_sensitive: Whether search is case-sensitive (default: True)
        max_results: Maximum number of results to return (default: None for all)
        include_pattern: File pattern to include (e.g., "*.py", "*.{js,ts}")

    Returns:
        Newline-separated results in format "filepath:line_number:matching_line"
        Returns "No results found." if no matches.

    Note:
        Automatically excludes binary files and common non-project directories.
        Respects .gitignore when using external tools (ripgrep, ag).
    """

    if not pattern:
        return "Error: Pattern cannot be empty"

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Grep", directory, pattern=pattern)

    directory = directory or "."
    orig_dir = os.getcwd()

    try:
        os.chdir(os.path.expanduser(directory))

        result = await _grep_with_ripgrep(pattern, case_sensitive, max_results, include_pattern)
        if result is not None:
            return result

        result = await _grep_with_ag(pattern, case_sensitive, max_results, include_pattern)
        if result is not None:
            return result

        result = await _grep_with_unix_grep(pattern, case_sensitive, max_results, include_pattern)
        if result is not None:
            return result

        return await _grep_with_python(pattern, case_sensitive, max_results, include_pattern)

    except FileNotFoundError:
        return f"Error: Directory '{directory}' does not exist. Please check the path."
    except PermissionError:
        return f"Error: Permission denied accessing directory '{directory}'"
    except Exception as e:
        return f"Error accessing directory '{directory}': {str(e)}"
    finally:
        os.chdir(orig_dir)
