"""
Module: sidekick.tools.update_file

File update tool for agent operations in the Sidekick application.
Enables safe text replacement in existing files with target/patch semantics.
"""

import os

from pydantic_ai.exceptions import ModelRetry

from sidekick.types import FileContent, FilePath, ToolResult
from sidekick.ui.output import info
from sidekick.ui.panels import error


async def update_file(filepath: FilePath, target: FileContent, patch: FileContent) -> ToolResult:
    """
    Update an existing file by replacing a target text block with a patch.
    Requires confirmation with diff before applying.

    Args:
        filepath (FilePath): The path to the file to update.
        target (FileContent): The entire, exact block of text to be replaced.
        patch (FileContent): The new block of text to insert.

    Returns:
        ToolResult: A message indicating the success or failure of the operation.
    """
    try:
        # Format arguments, truncating target and patch for display
        args = [repr(filepath)]
        if target is not None:
            if len(target) > 50:
                args.append(f"target='{target[:47]}...'")
            else:
                args.append(f"target={repr(target)}")
        if patch is not None:
            if len(patch) > 50:
                args.append(f"patch='{patch[:47]}...'")
            else:
                args.append(f"patch={repr(patch)}")
        args_display = ", ".join(args)

        await info(f"Update({args_display})")

        if not os.path.exists(filepath):
            raise ModelRetry(
                f"File '{filepath}' not found. Cannot update. "
                "Verify the filepath or use `write_file` if it's a new file."
            )

        with open(filepath, "r", encoding="utf-8") as f:
            original = f.read()

        if target not in original:
            # Provide context to help the LLM find the target
            context_lines = 10
            lines = original.splitlines()
            snippet = "\n".join(lines[:context_lines])
            # Use ModelRetry to guide the LLM
            raise ModelRetry(
                f"Target block not found in '{filepath}'. "
                "Ensure the `target` argument exactly matches the content you want to replace. "
                f"File starts with:\n---\n{snippet}\n---"
            )

        new_content = original.replace(target, patch, 1)

        if original == new_content:
            raise ModelRetry(
                f"Update target found, but replacement resulted in no changes to '{filepath}'. "
                "Was the `target` identical to the `patch`? Please check the file content."
            )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"File '{filepath}' updated successfully."

    except ModelRetry:
        # Re-raise ModelRetry for pydantic-ai to handle
        raise
    except Exception as update_error:
        err_msg = f"Error updating file '{filepath}': {update_error}"
        await error(err_msg)
        return err_msg
