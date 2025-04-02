import os

from pydantic_ai.exceptions import ModelRetry

from sidekick.utils import ui


def update_file(filepath: str, target: str, patch: str) -> str:
    """
    Update an existing file by replacing a target text block with a patch.
    Requires confirmation with diff before applying.

    Args:
        filepath (str): The path to the file to update.
        target (str): The entire, exact block of text to be replaced.
        patch (str): The new block of text to insert.

    Returns:
        str: A message indicating the success or failure of the operation.
    """
    try:
        if not os.path.exists(filepath):
            raise ModelRetry(
                f"File '{filepath}' not found. Cannot update. "
                "Verify the filepath or use `write_file` if it's a new file."
            )

        ui.status(f"Update({filepath})")
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

        new_content = original.replace(target, patch, 1)  # Replace only the first occurrence

        if original == new_content:
            # This could happen if target and patch are identical
            raise ModelRetry(
                f"Update target found, but replacement resulted in no changes to '{filepath}'. "
                "Was the `target` identical to the `patch`? Please check the file content."
            )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"File '{filepath}' updated successfully."
    except ModelRetry as e:
        ui.warning(str(e))
        raise e  # Re-raise
    except Exception as e:
        err_msg = f"Error updating file '{filepath}': {e}"
        ui.error(err_msg)
        return err_msg
