"""
Module: sidekick.tools.write_file

File writing tool for agent operations in the Sidekick application.
Creates new files with automatic directory creation and overwrite protection.
"""

import os

from pydantic_ai.exceptions import ModelRetry

from sidekick.types import FileContent, FilePath, ToolResult
from sidekick.ui.output import info
from sidekick.ui.panels import error


async def write_file(filepath: FilePath, content: FileContent) -> ToolResult:
    """
    Write content to a new file. Fails if the file already exists.
    Requires confirmation before writing.

    Args:
        filepath (FilePath): The path to the file to write to.
        content (FileContent): The content to write to the file.

    Returns:
        ToolResult: A message indicating the success or failure of the operation.
    """
    try:
        # Format args for logging, truncating content for display
        if content is not None and len(content) > 50:
            args_display = f"{repr(filepath)}, content='{content[:47]}...'"
        else:
            args_display = f"{repr(filepath)}, content={repr(content)}"

        await info(f"Write({args_display})")

        # Prevent overwriting existing files with this tool.
        if os.path.exists(filepath):
            # Use ModelRetry to guide the LLM
            raise ModelRetry(
                f"File '{filepath}' already exists. "
                "Use the `update_file` tool to modify it, or choose a different filepath."
            )

        # Create directories if they don't exist
        dirpath = os.path.dirname(filepath)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)

        return f"Successfully wrote to new file: {filepath}"

    except ModelRetry:
        # Re-raise ModelRetry for pydantic-ai to handle
        raise
    except Exception as write_error:
        err_msg = f"Error writing file '{filepath}': {write_error}"
        await error(err_msg)
        return err_msg
