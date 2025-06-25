import asyncio
import os
import re
import shutil
from pathlib import Path
from typing import Optional, Set

from pydantic_ai import RunContext

from sidekick.deps import ToolDeps

# Comprehensive list of directories to exclude from searches
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

# File extensions to treat as binary (skip in grep)
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
    pattern: str, case_sensitive: bool = True, max_count: Optional[int] = None
) -> Optional[str]:
    """Use ripgrep (fastest, respects .gitignore by default)."""
    if not shutil.which("rg"):
        return None

    command = ["rg", "-n"]  # -n for line numbers

    # Case sensitivity
    if not case_sensitive:
        command.append("-i")

    # Max results
    if max_count:
        command.extend(["-m", str(max_count)])

    # Pattern and path
    command.extend(["--", pattern, "."])

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        # ripgrep returns 1 when no matches found, which is not an error
        if process.returncode == 0 or (process.returncode == 1 and not stderr.strip()):
            output = stdout.decode().strip()
            return output or "No results found."
    except Exception:
        pass

    return None


async def _grep_with_ag(
    pattern: str, case_sensitive: bool = True, max_count: Optional[int] = None
) -> Optional[str]:
    """Use ag (The Silver Searcher) - fast and respects .gitignore."""
    if not shutil.which("ag"):
        return None

    command = ["ag", "--numbers"]  # --numbers for line numbers

    # Case sensitivity
    if not case_sensitive:
        command.append("-i")

    # Max results
    if max_count:
        command.extend(["-m", str(max_count)])

    # Pattern and path
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
    pattern: str, case_sensitive: bool = True, max_count: Optional[int] = None
) -> Optional[str]:
    """Use traditional Unix grep with smart exclusions."""
    if not shutil.which("grep"):
        return None

    command = ["grep", "-r", "-n", "-I"]  # -r recursive, -n line numbers, -I skip binary

    # Case sensitivity
    if not case_sensitive:
        command.append("-i")

    # Max results (grep doesn't have a direct option, we'll limit in post-processing)

    # Add exclusions
    exclude_patterns = EXCLUDE_DIRS.copy()
    exclude_patterns.update(_get_gitignore_patterns())

    for directory in exclude_patterns:
        if "*" not in directory and "/" not in directory:
            command.append(f"--exclude-dir={directory}")

    # Add binary file exclusions
    for ext in BINARY_EXTENSIONS:
        command.append(f"--exclude=*{ext}")

    # Pattern and path
    command.extend([pattern, "."])

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        # grep returns 1 when no matches found, which is not an error
        if process.returncode == 0 or (process.returncode == 1 and not stderr.strip()):
            output = stdout.decode().strip()

            # Apply max_count if specified
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
    pattern: str, case_sensitive: bool = True, max_count: Optional[int] = None
) -> str:
    """Pure Python fallback implementation."""
    # Compile regex pattern
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Invalid regex pattern: {e}"

    # Get exclusion patterns
    exclude_patterns = EXCLUDE_DIRS.copy()
    exclude_patterns.update(_get_gitignore_patterns())

    results = []
    count = 0

    # Walk the directory tree
    for root, dirs, files in os.walk("."):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_patterns and not d.startswith(".")]

        # Skip if root contains excluded pattern
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

            # Skip binary files
            if any(file.endswith(ext) for ext in BINARY_EXTENSIONS):
                continue

            filepath = os.path.join(root, file)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            # Format: filepath:line_number:line_content
                            result_line = f"{filepath}:{line_num}:{line.rstrip()}"
                            results.append(result_line)
                            count += 1

                            if max_count and count >= max_count:
                                break
            except (OSError, PermissionError):
                # Skip files we can't read
                continue

    return "\n".join(results) if results else "No results found."


async def grep(ctx: RunContext[ToolDeps], pattern: str) -> str:  # noqa: N802
    """Search for a text pattern inside files.

    If [`ripgrep`](https://github.com/BurntSushi/ripgrep) (rg) is available it will be
    used because it is significantly faster and honours `.gitignore` out-of-the-box.
    Otherwise a recursive `grep -rnI` fallback is used with a curated list of
    directories excluded to avoid extra noise and reduce token usage.
    """

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Grep", pattern)

    # Try tools in order of preference (speed and features)

    # 1. Try ripgrep (fastest, best features, respects .gitignore)
    result = await _grep_with_ripgrep(pattern)
    if result is not None:
        return result

    # 2. Try ag/silver searcher (fast, respects .gitignore)
    result = await _grep_with_ag(pattern)
    if result is not None:
        return result

    # 3. Try traditional Unix grep
    result = await _grep_with_unix_grep(pattern)
    if result is not None:
        return result

    # 4. Fall back to pure Python (works everywhere)
    return await _grep_with_python(pattern)
