from pydantic_ai import RunContext

from sidekick.deps import ToolDeps


async def read_file(ctx: RunContext[ToolDeps], filepath: str) -> str:
    """Read the contents of a file."""
    if ctx.deps and ctx.deps.display_tool_status:
        await ctx.deps.display_tool_status("Read", filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        return f"Error: File not found: {filepath}"
    except PermissionError:
        return f"Error: Permission denied: {filepath}"
    except Exception as e:
        return f"Error reading file {filepath}: {str(e)}"
