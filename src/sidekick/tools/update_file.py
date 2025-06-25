import asyncio

from pydantic_ai import ModelRetry, RunContext

from sidekick import ui
from sidekick.deps import ToolDeps


async def update_file(
    ctx: RunContext[ToolDeps], filepath: str, old_content: str, new_content: str
) -> str:
    """Update specific content in a file."""
    if old_content == new_content:
        raise ModelRetry(
            "The old_content and new_content are identical. "
            "Please provide different content for the replacement."
        )

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        raise ModelRetry(f"File not found: {filepath}. Please check the file path and try again.")
    except Exception as e:
        raise ModelRetry(f"Error reading file {filepath}: {str(e)}")

    if old_content not in content:
        preview = old_content[:100] + "..." if len(old_content) > 100 else old_content
        raise ModelRetry(
            f"Content to replace not found in {filepath}. "
            f"Searched for: '{preview}'. "
            "Please re-read the file and ensure the exact content matches, including whitespace."
        )

    if ctx.deps and ctx.deps.confirm_action:
        updated_content = content.replace(old_content, new_content, 1)
        diff_preview = ui.create_unified_diff(content, updated_content, filepath)
        footer = f"File: {filepath}"

        if not await ctx.deps.confirm_action("Update File", diff_preview, footer):
            raise asyncio.CancelledError("Tool execution cancelled by user")

    try:
        updated_content = content.replace(old_content, new_content, 1)
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(updated_content)
    except Exception as e:
        raise ModelRetry(f"Error writing to file {filepath}: {str(e)}")

    return f"Successfully updated {filepath}"
