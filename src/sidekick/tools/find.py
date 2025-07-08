import asyncio
import fnmatch
import os
import re
import shutil
from pathlib import Path
from typing import Optional, Set

from pydantic_ai import RunContext

from sidekick.deps import ToolDeps
from sidekick.tools.common import BINARY_EXTENSIONS, EXCLUDE_DIRS


def _get_gitignore_patterns() -> Set[str]:
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        return set()

    patterns = set()
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line)
    except Exception:
        pass

    return patterns


async def _find_files_with_fd(pattern: str, dirs: bool, max_depth: Optional[int]) -> Optional[str]:
    if not shutil.which("fd"):
        return None

    cmd = ["fd"]
    if dirs:
        cmd.extend(["--type", "d"])
    else:
        cmd.extend(["--type", "f"])

    if max_depth:
        cmd.extend(["--max-depth", str(max_depth)])

    cmd.append(pattern)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            output = stdout.decode().strip()
            return output if output else "No results found."
        return None
    except Exception:
        return None


async def _find_files_with_rg(pattern: str, max_depth: Optional[int]) -> Optional[str]:
    if not shutil.which("rg"):
        return None

    cmd = ["rg", "--files"]
    if max_depth:
        cmd.extend(["--max-depth", str(max_depth)])

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            files = stdout.decode().strip().split("\n")
            matching = [f for f in files if fnmatch.fnmatch(f, pattern)]
            return "\n".join(matching) if matching else "No results found."
        return None
    except Exception:
        return None


async def _find_content_with_rg(
    content: str,
    include_pattern: Optional[str] = None,
    case_sensitive: bool = True,
    max_results: Optional[int] = None,
) -> Optional[str]:
    if not shutil.which("rg"):
        return None

    cmd = ["rg", "--line-number"]

    if not case_sensitive:
        cmd.append("-i")

    if include_pattern:
        cmd.extend(["--glob", include_pattern])

    if max_results:
        cmd.extend(["--max-count", str(max_results)])

    cmd.append(content)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            output = stdout.decode().strip()
            return output if output else "No results found."
        elif process.returncode == 1:
            return "No results found."
        return None
    except Exception:
        return None


async def _find_content_with_ag(
    content: str,
    include_pattern: Optional[str] = None,
    case_sensitive: bool = True,
    max_results: Optional[int] = None,
) -> Optional[str]:
    if not shutil.which("ag"):
        return None

    cmd = ["ag", "--line-numbers"]

    if not case_sensitive:
        cmd.append("-i")

    if include_pattern:
        cmd.extend(["-G", include_pattern])

    if max_results:
        cmd.extend(["--max-count", str(max_results)])

    cmd.append(content)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            output = stdout.decode().strip()
            return output if output else "No results found."
        elif process.returncode == 1:
            return "No results found."
        return None
    except Exception:
        return None


def _find_files_python(pattern: str, dirs: bool, max_depth: Optional[int]) -> str:
    exclude_patterns = EXCLUDE_DIRS.copy()
    exclude_patterns.update(_get_gitignore_patterns())

    results = []
    for root, directories, files in os.walk(".", followlinks=False):
        current_depth = root.count(os.sep)
        if max_depth and current_depth >= max_depth:
            directories[:] = []
            continue

        skip_root = False
        for exclude in exclude_patterns:
            if exclude in root:
                skip_root = True
                break
        if skip_root:
            continue

        directories[:] = [d for d in directories if d not in exclude_patterns]

        items = directories if dirs else files
        for item in items:
            if fnmatch.fnmatch(item, pattern):
                path = os.path.join(root, item)
                results.append(path)

    return "\n".join(sorted(results)) if results else "No results found."


def _find_content_python(
    pattern: str,
    include_pattern: Optional[str] = None,
    case_sensitive: bool = True,
    max_results: Optional[int] = None,
) -> str:
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
            if max_results and count >= max_results:
                results.append(f"... (showing first {max_results} results)")
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

                            if max_results and count >= max_results:
                                break
            except (OSError, PermissionError):
                continue

    return "\n".join(results) if results else "No results found."


async def find(
    ctx: RunContext[ToolDeps],
    directory: str = ".",
    pattern: str = "*",
    *,
    content: Optional[str] = None,
    dirs: bool = False,
    max_depth: Optional[int] = None,
    case_sensitive: bool = True,
    max_results: Optional[int] = None,
    include_pattern: Optional[str] = None,
) -> str:
    """Find files/directories by name or content.

    Examples:
        find(".", "*.py")                    # Find all Python files
        find("src", "*test*")                # Find files with "test" in name under src/
        find(".", "*config*", dirs=True)     # Find directories with "config" in name
        find(".", "*.js", max_depth=2)       # Find JS files, max 2 levels deep
        find(".", content="TODO")            # Find all files containing "TODO"
        find(".", "*.py", content="def main") # Find Python files containing "def main"
        find(".", content="error", case_sensitive=False) # Case-insensitive content search

    Args:
        directory: Directory to search in (default: current directory ".")
        pattern: Shell-style wildcard pattern for filename (default: "*" matches all)
            - * matches any characters (e.g., "*.py" matches all .py files)
            - ? matches single character (e.g., "test?.py" matches test1.py, test2.py)
            - [seq] matches any character in seq (e.g., "test[123].py")
        content: Text or regex pattern to search for in file contents
        dirs: If True, search for directories instead of files (default: False)
        max_depth: Maximum depth to search (default: None for unlimited)
        case_sensitive: Whether content search is case-sensitive (default: True)
        max_results: Maximum number of results to return (default: None for all)
        include_pattern: When searching content, only search files matching this pattern

    Returns:
        For name search: Newline-separated list of matching paths
        For content search: Newline-separated results in format "filepath:line_number:matching_line"
        Returns "No results found." if no matches.

    Note:
        Automatically excludes common non-project directories (node_modules, .git, etc.)
        and respects .gitignore when using external tools.
    """

    if ctx.deps and ctx.deps.display_tool_status:
        status_info = {"pattern": pattern, "dirs": dirs, "depth": max_depth}
        if content:
            status_info["content"] = content
        await ctx.deps.display_tool_status("Find", directory, **status_info)

    directory = directory or "."
    orig_dir = os.getcwd()

    try:
        os.chdir(os.path.expanduser(directory))

        if content:
            result = await _find_content_with_rg(
                content, include_pattern, case_sensitive, max_results
            )
            if result is not None:
                return result

            result = await _find_content_with_ag(
                content, include_pattern, case_sensitive, max_results
            )
            if result is not None:
                return result

            return _find_content_python(content, include_pattern, case_sensitive, max_results)
        else:
            result = await _find_files_with_fd(pattern, dirs, max_depth)
            if result is not None:
                return result

            if not dirs:
                result = await _find_files_with_rg(pattern, max_depth)
                if result is not None:
                    return result

            return _find_files_python(pattern, dirs, max_depth)

    finally:
        os.chdir(orig_dir)
