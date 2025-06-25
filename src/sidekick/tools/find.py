import asyncio
import fnmatch
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


def _get_gitignore_patterns() -> Set[str]:
    """Read .gitignore patterns if it exists."""
    patterns = set()
    gitignore_path = Path(".gitignore")

    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith("#"):
                        # Simple conversion - full gitignore parsing is complex
                        if line.endswith("/"):
                            # Directory pattern
                            patterns.add(line.rstrip("/"))
                        else:
                            patterns.add(line)
        except Exception:
            # Silently ignore gitignore parsing errors
            pass

    return patterns


def _should_skip_path(path: Path, exclude_patterns: Set[str]) -> bool:
    """Check if a path should be skipped based on exclusion patterns."""
    path_str = str(path)

    # Check each component of the path
    for part in path.parts:
        if part in exclude_patterns:
            return True
        # Check glob patterns
        for pattern in exclude_patterns:
            if "*" in pattern and fnmatch.fnmatch(part, pattern):
                return True

    # Check full path patterns
    for pattern in exclude_patterns:
        if "/" in pattern and fnmatch.fnmatch(path_str, pattern):
            return True

    return False


async def _find_with_fd(
    pattern: str, search_for_dirs: bool, max_depth: Optional[int] = None
) -> Optional[str]:
    """Use fd (fast find alternative) if available."""
    if not shutil.which("fd"):
        return None

    command = ["fd"]

    # Type flag
    if search_for_dirs:
        command.extend(["--type", "d"])
    else:
        command.extend(["--type", "f"])

    # Max depth
    if max_depth:
        command.extend(["--max-depth", str(max_depth)])

    # Pattern
    command.append(pattern)

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout.decode().strip() or "No results found."
    except Exception:
        pass

    return None


async def _find_with_rg(
    pattern: str, search_for_dirs: bool, max_depth: Optional[int] = None
) -> Optional[str]:
    """Use ripgrep to find files (it's fast and respects .gitignore)."""
    if not shutil.which("rg"):
        return None

    command = ["rg", "--files", "--hidden", "--glob", pattern]

    if max_depth:
        command.extend(["--max-depth", str(max_depth)])

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            output = stdout.decode().strip()

            # If searching for directories, extract unique directories
            if search_for_dirs and output:
                lines = output.splitlines()
                dirs = set()
                for line in lines:
                    # Check if the line itself matches the pattern as a directory
                    path = Path(line)
                    if path.is_dir() and fnmatch.fnmatch(path.name, pattern):
                        dirs.add(str(path))
                    # Also check parent directories
                    for parent in path.parents:
                        if parent != Path(".") and fnmatch.fnmatch(parent.name, pattern):
                            dirs.add(str(parent))
                output = "\n".join(sorted(dirs)) if dirs else ""

            return output or "No results found."
    except Exception:
        pass

    return None


async def _find_with_unix_find(
    pattern: str, search_for_dirs: bool, max_depth: Optional[int] = None
) -> Optional[str]:
    """Use traditional Unix find command."""
    if not shutil.which("find"):
        return None

    command = ["find", "."]

    # Add max depth if specified
    if max_depth:
        command.extend(["-maxdepth", str(max_depth)])

    # Build exclusion list - combine defaults with gitignore
    exclude_patterns = EXCLUDE_DIRS.copy()
    exclude_patterns.update(_get_gitignore_patterns())

    # Build the exclusion block
    if exclude_patterns:
        command.append("(")
        for idx, pattern_to_exclude in enumerate(exclude_patterns):
            if idx:
                command.append("-o")

            if "*" in pattern_to_exclude:
                command.extend(["-name", pattern_to_exclude])
            elif "/" in pattern_to_exclude:
                command.extend(["-path", f"./{pattern_to_exclude}"])
            else:
                command.extend(["-path", f"./{pattern_to_exclude}"])

        command.extend([")", "-prune", "-o"])

    # Primary expression
    search_type = "d" if search_for_dirs else "f"
    command.extend(["-type", search_type, "-name", pattern, "-print"])

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0 or (process.returncode == 1 and not stderr):
            return stdout.decode().strip() or "No results found."
    except Exception:
        pass

    return None


async def _find_with_python(
    pattern: str, search_for_dirs: bool, max_depth: Optional[int] = None
) -> str:
    """Pure Python fallback implementation."""
    # Build exclusion set
    exclude_patterns = EXCLUDE_DIRS.copy()
    exclude_patterns.update(_get_gitignore_patterns())

    results = []
    root_path = Path(".")

    # Walk the directory tree
    for path in root_path.rglob("*"):
        # Check depth
        if max_depth is not None:
            try:
                depth = len(path.relative_to(root_path).parts)
                if depth > max_depth:
                    continue
            except ValueError:
                continue

        # Skip excluded paths
        if _should_skip_path(path, exclude_patterns):
            continue

        # Check if it matches our criteria
        try:
            if search_for_dirs and path.is_dir():
                if fnmatch.fnmatch(path.name, pattern):
                    results.append(str(path))
            elif not search_for_dirs and path.is_file():
                if fnmatch.fnmatch(path.name, pattern):
                    results.append(str(path))
        except (OSError, PermissionError):
            # Skip inaccessible paths
            continue

    # Sort results for consistency
    results.sort()

    return "\n".join(results) if results else "No results found."


async def find(ctx: RunContext[ToolDeps], pattern: str, *, dirs: bool = False) -> str:  # noqa: N802
    """find files (or directories) by name using a wildcard pattern.

    By default it returns matching **files**. Pass `dirs=True` to look for
    directories instead. Internally it delegates to the Unix `find` command with
    a set of excluded directories so that searches stay focused on relevant
    project files.
    """

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Find", pattern)

    # Try tools in order of preference (speed and features)

    # 1. Try fd (fastest, respects .gitignore, cross-platform)
    result = await _find_with_fd(pattern, dirs)
    if result is not None:
        return result

    # 2. Try ripgrep (fast, respects .gitignore, but primarily for file content)
    if not dirs:  # rg is not great for finding directories
        result = await _find_with_rg(pattern, dirs)
        if result is not None:
            return result

    # 3. Try traditional Unix find
    result = await _find_with_unix_find(pattern, dirs)
    if result is not None:
        return result

    # 4. Fall back to pure Python (works everywhere)
    return await _find_with_python(pattern, dirs)
