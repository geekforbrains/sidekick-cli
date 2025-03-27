import os

from pydantic_ai.exceptions import ModelRetry

from sidekick.utils import ui


def write_file(filepath: str, content: str) -> str:
    """
    Write content to a new file. Fails if the file already exists.
    Requires confirmation before writing.

    Args:
        filepath (str): The path to the file to write to.
        content (str): The content to write to the file.

    Returns:
        str: A message indicating the success or failure of the operation.
    """
    try:
        # Prevent overwriting existing files with this tool.
        if os.path.exists(filepath):
            # Use ModelRetry to guide the LLM
            raise ModelRetry(
                f"File '{filepath}' already exists. "
                "Use the `update_file` tool to modify it, or choose a different filepath."
            )

        # Confirmation should be handled by the LLM/user interaction layer before calling.
        # This tool assumes confirmation was obtained if required by the overall process.
        ui.status(f"Write({filepath})")

        # Create directories if they don't exist
        dirpath = os.path.dirname(filepath)
        if dirpath and not os.path.exists(dirpath):
            ui.debug(f"Creating directory: {dirpath}")
            os.makedirs(dirpath, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)

        success_msg = f"Successfully wrote to new file: {filepath}"
        return success_msg

    except ModelRetry as e:
        # Log ModelRetry messages from this tool as warnings
        ui.warning(str(e))
        raise e  # Re-raise to be handled by pydantic-ai
    except Exception as e:
        err_msg = f"Error writing file '{filepath}': {e}"
        ui.error(err_msg)
        return err_msg
