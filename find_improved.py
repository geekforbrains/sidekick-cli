import asyncio
import os
from pathlib import Path
from typing import Optional

from pydantic_ai import RunContext

from sidekick.deps import ToolDeps

# Default directories to exclude
DEFAULT_EXCLUDE_DIRS = [
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".coverage",
    "htmlcov",
    ".idea",
    ".vscode",
    "target",  # Rust/Java
    "out",     # Various build systems
    ".next",   # Next.js
    ".nuxt",   # Nuxt.js
    "coverage",
    ".turbo",
    ".parcel-cache",
    "tmp",
    "temp",
    ".cache",
    ".DS_Store",
    "Thumbs.db",
    ".sass-cache",
    "bower_components",
    "vendor",  # PHP/Ruby
    "*.egg-info",
    "__pycache__",
]


def _get_gitignore_patterns() -> list[str]:
    """Read .gitignore patterns if it exists."""
    patterns = []
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith("#"):
                    # Convert gitignore patterns to find-compatible paths
                    # This is simplified - full gitignore parsing is complex
                    if "/" in line:
                        patterns.append(line.lstrip("/"))
                    else:
                        patterns.append(line)
    return patterns


def _build_find_command(
    pattern: str, 
    search_for_dirs: bool,
    max_depth: Optional[int] = None,
    path: str = ".",
    respect_gitignore: bool = True
) -> list[str]:
    """Construct a portable `find` command excluding noisy directories."""
    command: list[str] = ["find", path]
    
    # Add max depth if specified
    if max_depth is not None:
        command.extend(["-maxdepth", str(max_depth)])
    
    # Build exclusion list
    exclude_dirs = DEFAULT_EXCLUDE_DIRS.copy()
    
    # Optionally add gitignore patterns
    if respect_gitignore:
        gitignore_patterns = _get_gitignore_patterns()
        exclude_dirs.extend(gitignore_patterns)
    
    # Remove duplicates while preserving order
    exclude_dirs = list(dict.fromkeys(exclude_dirs))

    # Build the exclusion block
    if exclude_dirs:
        command.append("(")
        for idx, d in enumerate(exclude_dirs):
            if idx:  # first element doesn't need `-o`
                command.append("-o")
            
            # Handle different pattern types
            if "*" in d or "?" in d:
                # It's a glob pattern
                command.extend(["-name", d])
            else:
                # It's a directory path
                if d.startswith("/"):
                    command.extend(["-path", f".{d}"])
                else:
                    command.extend(["-path", f"./{d}"])
        
        command.extend([")", "-prune", "-o"])

    # Primary expression – file vs dir search
    search_type = "d" if search_for_dirs else "f"
    command.extend(["-type", search_type, "-name", pattern, "-print"])

    return command


async def _run_find_command(command: list[str]) -> str:
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        # Some find implementations write warnings to stderr that aren't errors
        # (e.g., permission denied for certain directories)
        if process.returncode != 0 and stderr:
            return f"Error executing find command:\n{stderr.decode().strip()}"
            
        output = stdout.decode().strip()
        
        # Filter out any excluded paths that might have slipped through
        # (belt and suspenders approach)
        if output:
            lines = output.splitlines()
            filtered_lines = []
            for line in lines:
                should_exclude = False
                for exclude_dir in DEFAULT_EXCLUDE_DIRS:
                    if f"/{exclude_dir}/" in line or line.endswith(f"/{exclude_dir}"):
                        should_exclude = True
                        break
                if not should_exclude:
                    filtered_lines.append(line)
            output = "\n".join(filtered_lines)
        
        return output or "No results found."
    except FileNotFoundError:
        # Fallback to Python implementation if find is not available
        return await _python_find_fallback(pattern, search_for_dirs)


async def _python_find_fallback(pattern: str, search_for_dirs: bool) -> str:
    """Pure Python fallback for systems without Unix find."""
    import fnmatch
    
    results = []
    for root, dirs, files in os.walk("."):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDE_DIRS]
        
        # Search in the appropriate list
        items = dirs if search_for_dirs else files
        
        for item in items:
            if fnmatch.fnmatch(item, pattern):
                path = os.path.join(root, item)
                # Normalize path separators and remove leading ./
                path = path.replace("\\", "/")
                if path.startswith("./"):
                    path = path[2:]
                results.append(path)
    
    return "\n".join(results) if results else "No results found."


async def find(
    ctx: RunContext[ToolDeps], 
    pattern: str, 
    *, 
    dirs: bool = False,
    max_depth: Optional[int] = None,
    path: str = ".",
    respect_gitignore: bool = True
) -> str:
    """find files (or directories) by name using a wildcard pattern.

    By default it returns matching **files**. Pass `dirs=True` to look for
    directories instead. Internally it delegates to the Unix `find` command with
    a set of excluded directories so that searches stay focused on relevant
    project files. Falls back to Python implementation on Windows.
    
    Args:
        pattern: Wildcard pattern to match (e.g., "*.py", "test_*")
        dirs: Search for directories instead of files
        max_depth: Maximum depth to search (None for unlimited)
        path: Starting path for search (default: current directory)
        respect_gitignore: Whether to respect .gitignore patterns
    """

    if ctx.deps and ctx.deps.display_tool_status:
        status_msg = f"Find {'directories' if dirs else 'files'}: {pattern}"
        if max_depth:
            status_msg += f" (max depth: {max_depth})"
        await ctx.deps.display_tool_status("Find", status_msg)

    command = _build_find_command(pattern, search_for_dirs=dirs, max_depth=max_depth, path=path, respect_gitignore=respect_gitignore)
    return await _run_find_command(command)