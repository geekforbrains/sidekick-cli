import asyncio
from pathlib import Path

from pydantic_ai import RunContext

from sidekick import ui
from sidekick.deps import ToolDeps


async def write_file(ctx: RunContext[ToolDeps], filepath: str, content: str) -> str:
    """Write content to a file."""
    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Write", filepath)

    if ctx.deps and ctx.deps.confirm_action:
        syntax = ui.create_syntax_highlighted(content, filepath)
        footer = f"File: {filepath}"
        if not await ctx.deps.confirm_action("Write File", syntax, footer):
            raise asyncio.CancelledError("Tool execution cancelled by user")

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)

    return f"Successfully wrote to {filepath}"
