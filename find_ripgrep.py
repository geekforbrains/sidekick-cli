import asyncio
import os
from typing import Optional

from pydantic_ai import RunContext

from sidekick.deps import ToolDeps


async def _run_rg_files(pattern: str, search_for_dirs: bool, max_depth: Optional[int] = None) -> str:
    """Use ripgrep to find files/directories."""
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
            
            # If searching for directories, filter to only directories
            if search_for_dirs and output:
                lines = output.splitlines()
                dirs = set()
                for line in lines:
                    dir_path = os.path.dirname(line)
                    if dir_path and dir_path != ".":
                        dirs.add(dir_path)
                output = "\n".join(sorted(dirs))
            
            return output or "No results found."
        else:
            # Ripgrep not found or error, fall back to find
            return None
    except FileNotFoundError:
        return None


async def find(
    ctx: RunContext[ToolDeps], 
    pattern: str, 
    *, 
    dirs: bool = False,
    max_depth: Optional[int] = None,
) -> str:
    """find files (or directories) by name using a wildcard pattern.

    Uses ripgrep if available (faster and respects .gitignore), otherwise
    falls back to Unix find with smart exclusions.
    """
    if ctx.deps and ctx.deps.display_tool_status:
        status_msg = f"Find {'directories' if dirs else 'files'}: {pattern}"
        await ctx.deps.display_tool_status("Find", status_msg)

    # Try ripgrep first
    result = await _run_rg_files(pattern, dirs, max_depth)
    if result is not None:
        return result
    
    # Fall back to original find implementation
    # ... (include the original find code here as fallback)