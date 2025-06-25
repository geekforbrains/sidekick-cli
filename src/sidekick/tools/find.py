import asyncio
import fnmatch
import os
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
                        if line.endswith("/"):
                            patterns.add(line.rstrip("/"))
                        else:
                            patterns.add(line)
        except Exception:
            pass

    return patterns


def _should_skip_path(path: Path, exclude_patterns: Set[str]) -> bool:
    """Check if a path should be skipped based on exclusion patterns."""
    path_str = str(path)

    for part in path.parts:
        if part in exclude_patterns:
            return True
        for pattern in exclude_patterns:
            if "*" in pattern and fnmatch.fnmatch(part, pattern):
                return True

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

    if search_for_dirs:
        command.extend(["--type", "d"])
    else:
        command.extend(["--type", "f"])

    if max_depth:
        command.extend(["--max-depth", str(max_depth)])

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

            if search_for_dirs and output:
                lines = output.splitlines()
                dirs = set()
                for line in lines:
                    path = Path(line)
                    if path.is_dir() and fnmatch.fnmatch(path.name, pattern):
                        dirs.add(str(path))
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

    if max_depth:
        command.extend(["-maxdepth", str(max_depth)])

    exclude_patterns = EXCLUDE_DIRS.copy()
    exclude_patterns.update(_get_gitignore_patterns())

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
    exclude_patterns = EXCLUDE_DIRS.copy()
    exclude_patterns.update(_get_gitignore_patterns())

    results = []
    root_path = Path(".")

    for path in root_path.rglob("*"):
        if max_depth is not None:
            try:
                depth = len(path.relative_to(root_path).parts)
                if depth > max_depth:
                    continue
            except ValueError:
                continue

        if _should_skip_path(path, exclude_patterns):
            continue

        try:
            if search_for_dirs and path.is_dir():
                if fnmatch.fnmatch(path.name, pattern):
                    results.append(str(path))
            elif not search_for_dirs and path.is_file():
                if fnmatch.fnmatch(path.name, pattern):
                    results.append(str(path))
        except (OSError, PermissionError):
            continue

    results.sort()

    return "\n".join(results) if results else "No results found."


async def find(
    ctx: RunContext[ToolDeps],
    directory: str = ".",
    pattern: str = "*",
    *,
    dirs: bool = False,
    max_depth: Optional[int] = None,
) -> str:  # noqa: N802
    """Find files or directories by name pattern.

    Examples:
        find(".", "*.py")           # Find all Python files
        find("src", "*test*")       # Find files with "test" in name under src/
        find(".", "*config*", dirs=True)  # Find directories with "config" in name
        find(".", "*.js", max_depth=2)    # Find JS files, max 2 levels deep

    Args:
        directory: Directory to search in (default: current directory ".")
        pattern: Shell-style wildcard pattern (default: "*" matches all)
            - * matches any characters (e.g., "*.py" matches all .py files)
            - ? matches single character (e.g., "test?.py" matches test1.py, test2.py)
            - [seq] matches any character in seq (e.g., "test[123].py")
            - *foo* matches any file containing "foo" in the name
        dirs: If True, search for directories instead of files (default: False)
        max_depth: Maximum depth to search (default: None for unlimited)

    Returns:
        Newline-separated list of matching paths, or "No results found."

    Note:
        Automatically excludes common non-project directories (node_modules, .git, etc.)
        and respects .gitignore when using external tools.
    """

    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status(
            "Find", directory, pattern=pattern, dirs=dirs, depth=max_depth
        )

    directory = directory or "."
    orig_dir = os.getcwd()

    try:
        os.chdir(os.path.expanduser(directory))

        result = await _find_with_fd(pattern, dirs, max_depth)
        if result is not None:
            return result

        if not dirs:
            result = await _find_with_rg(pattern, dirs, max_depth)
            if result is not None:
                return result

        result = await _find_with_unix_find(pattern, dirs, max_depth)
        if result is not None:
            return result

        return await _find_with_python(pattern, dirs, max_depth)

    finally:
        os.chdir(orig_dir)
