import asyncio
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from pydantic_ai import RunContext

from sidekick.deps import ToolDeps
from .search import EXCLUDE_DIRS


def _should_exclude(path: str, gitignore_patterns: List[str]) -> bool:
    """Check if a path should be excluded based on patterns."""
    path_obj = Path(path)

    # Check against EXCLUDE_DIRS
    for part in path_obj.parts:
        if part in EXCLUDE_DIRS:
            return True

    # Check against gitignore patterns (simplified)
    for pattern in gitignore_patterns:
        pattern = pattern.strip()
        if not pattern or pattern.startswith("#"):
            continue

        # Simple pattern matching (not full gitignore spec)
        if pattern.endswith("/"):
            # Directory pattern
            if pattern[:-1] in path_obj.parts:
                return True
        else:
            # File pattern
            if path_obj.match(pattern):
                return True

    return False


def _read_gitignore(base_path: str) -> List[str]:
    """Read .gitignore patterns from the given directory."""
    gitignore_path = os.path.join(base_path, ".gitignore")
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "r") as f:
                return f.readlines()
        except Exception:
            pass
    return []


def _format_tree(items: List[Tuple[str, bool, int]], prefix: str = "") -> List[str]:
    """Format directory structure as a tree."""
    lines = []
    for i, (name, is_dir, file_count) in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "

        if is_dir and file_count > 0:
            lines.append(f"{prefix}{current_prefix}{name}/ ({file_count} files)")
        elif is_dir:
            lines.append(f"{prefix}{current_prefix}{name}/")
        else:
            lines.append(f"{prefix}{current_prefix}{name}")

    return lines


async def _run_rg_files(path: str, max_depth: int) -> str:
    """Use ripgrep to list files efficiently."""
    cmd = ["rg", "--files", "--max-depth", str(max_depth), path]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            files = stdout.decode().strip().split("\n")
            # Convert flat file list to tree structure
            return _build_tree_from_files(files, path)
        else:
            # Fall back to Python implementation
            return None
    except Exception:
        return None


def _build_tree_from_files(files: List[str], base_path: str) -> str:
    """Build a tree structure from a flat list of file paths."""
    # This is a simplified version - for now, fallback to Python implementation
    # A full implementation would parse the paths and build a proper tree
    return None


def _walk_directory(
    path: str, max_depth: int, current_depth: int = 0, gitignore_patterns: List[str] = None
) -> Tuple[List[str], Dict[str, int]]:
    """Walk directory and return formatted tree lines and stats."""
    if gitignore_patterns is None:
        gitignore_patterns = _read_gitignore(path)

    lines = []
    total_files = 0
    total_dirs = 0

    if current_depth >= max_depth:
        return lines, {"files": total_files, "dirs": total_dirs}

    try:
        items = []
        for item in sorted(os.listdir(path)):
            if item.startswith(".") and item not in [".gitignore", ".env.example"]:
                continue

            item_path = os.path.join(path, item)
            if _should_exclude(item_path, gitignore_patterns):
                continue

            is_dir = os.path.isdir(item_path)
            file_count = 0

            if is_dir:
                # Count files in subdirectory (for display)
                try:
                    sub_items = os.listdir(item_path)
                    file_count = sum(
                        1
                        for i in sub_items
                        if not os.path.isdir(os.path.join(item_path, i)) and not i.startswith(".")
                    )
                except Exception:
                    pass
                total_dirs += 1
            else:
                total_files += 1

            items.append((item, is_dir, file_count))

        # Sort: directories first, then files
        items.sort(key=lambda x: (not x[1], x[0].lower()))

        # Format current level
        if current_depth == 0:
            lines.append(f"{path}")

        # Add tree lines
        tree_lines = _format_tree(items)
        lines.extend(tree_lines)

        # Recursively process subdirectories
        for i, (name, is_dir, _) in enumerate(items):
            if is_dir:
                item_path = os.path.join(path, name)
                is_last = i == len(items) - 1
                prefix = "    " if is_last else "│   "

                sub_lines, sub_stats = _walk_directory(
                    item_path, max_depth, current_depth + 1, gitignore_patterns
                )

                # Add subdirectory content with proper indentation
                for line in sub_lines:
                    if line:  # Skip empty lines
                        lines.append(prefix + line)

                total_files += sub_stats["files"]
                total_dirs += sub_stats["dirs"]

    except PermissionError:
        lines.append(f"Permission denied: {path}")
    except Exception as e:
        lines.append(f"Error reading directory: {str(e)}")

    return lines, {"files": total_files, "dirs": total_dirs}


async def list_directory(ctx: RunContext[ToolDeps], path: str = ".", max_depth: int = 3) -> str:
    """
    List directory contents in a tree structure, respecting .gitignore and common exclusions.

    Args:
        path: Directory path to list (default: current directory)
        max_depth: Maximum depth to traverse (default: 3)

    Returns:
        Formatted directory tree as a string
    """
    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("List", path, depth=max_depth)

    path = os.path.abspath(os.path.expanduser(path))

    if not os.path.exists(path):
        return f"Error: Path does not exist: {path}"

    if not os.path.isdir(path):
        return f"Error: Path is not a directory: {path}"

    # Try using ripgrep first if available
    if shutil.which("rg"):
        result = await _run_rg_files(path, max_depth)
        if result:
            return result

    # Fall back to Python implementation
    lines, stats = _walk_directory(path, max_depth)

    # Give AI the context of result
    lines.append("")
    lines.append(f"Total: {stats['files']} files, {stats['dirs']} directories")
    return "\n".join(lines)
