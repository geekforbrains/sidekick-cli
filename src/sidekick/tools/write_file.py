import asyncio
import logging
from pathlib import Path

from pydantic_ai import RunContext

from sidekick import ui
from sidekick.deps import ToolDeps

log = logging.getLogger(__name__)


async def write_file(ctx: RunContext[ToolDeps], filepath: str, content: str) -> str:
    """Write content to a file."""
    log.debug(f"write_file called with filepath: {filepath}, content length: {len(content)}")

    # Write content is in a panel already, showing this here feels redundant
    # Commenting out for now
    #
    # if ctx.deps and ctx.deps.display_tool_status:
    #     await ctx.deps.display_tool_status("Write", filepath)

    if ctx.deps and ctx.deps.confirm_action:
        syntax = ui.create_syntax_highlighted(content, filepath)
        footer = f"File: {filepath}"
        if not await ctx.deps.confirm_action("Write File", syntax, footer):
            raise asyncio.CancelledError("Tool execution cancelled by user")

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)

    return f"Successfully wrote to {filepath}"
