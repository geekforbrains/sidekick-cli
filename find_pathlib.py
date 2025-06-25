import asyncio
from pathlib import Path
from typing import Optional, Set
import fnmatch

from pydantic_ai import RunContext

from sidekick.deps import ToolDeps

# Directories to skip
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv", "env", 
    "build", "dist", ".pytest_cache", ".mypy_cache", ".tox",
    ".coverage", "htmlcov", ".idea", ".vscode", "target", "out",
    ".next", ".nuxt", "coverage", ".turbo", ".parcel-cache",
    "tmp", "temp", ".cache", "bower_components", "vendor"
}


def _should_skip_path(path: Path, exclude_dirs: Set[str]) -> bool:
    """Check if a path should be skipped based on exclusion rules."""
    for part in path.parts:
        if part in exclude_dirs:
            return True
    return False


def _read_gitignore_patterns() -> Set[str]:
    """Read and parse .gitignore patterns."""
    patterns = set()
    gitignore_path = Path(".gitignore")
    
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Simple conversion - full gitignore support is complex
                    if "/" not in line:
                        patterns.add(line)
    
    return patterns


async def find(
    ctx: RunContext[ToolDeps], 
    pattern: str, 
    *, 
    dirs: bool = False,
    max_depth: Optional[int] = None,
    respect_gitignore: bool = True
) -> str:
    """find files (or directories) by name using a wildcard pattern.
    
    Pure Python implementation using pathlib - works on all platforms.
    """
    if ctx.deps and ctx.deps.display_tool_status:
        status_msg = f"Find {'directories' if dirs else 'files'}: {pattern}"
        await ctx.deps.display_tool_status("Find", status_msg)
    
    # Build exclusion set
    exclude_dirs = EXCLUDE_DIRS.copy()
    if respect_gitignore:
        exclude_dirs.update(_read_gitignore_patterns())
    
    results = []
    root_path = Path(".")
    
    # Use rglob for recursive search with depth control
    for path in root_path.rglob("*"):
        # Check depth
        if max_depth is not None:
            depth = len(path.relative_to(root_path).parts)
            if depth > max_depth:
                continue
        
        # Skip excluded paths
        if _should_skip_path(path, exclude_dirs):
            continue
        
        # Check if it matches our criteria
        if dirs and path.is_dir():
            if fnmatch.fnmatch(path.name, pattern):
                results.append(str(path))
        elif not dirs and path.is_file():
            if fnmatch.fnmatch(path.name, pattern):
                results.append(str(path))
    
    # Sort results for consistency
    results.sort()
    
    return "\n".join(results) if results else "No results found."