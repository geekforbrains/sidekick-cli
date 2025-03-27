import os

from sidekick.utils import ui


def read_file(filepath: str) -> str:
    """
    Read the contents of a file.

    Args:
        filepath (str): The path to the file to read.

    Returns:
        str: The contents of the file or an error message.
    """
    ui.status(f"Read({filepath})")
    try:
        # Add a size limit to prevent reading huge files
        if os.path.getsize(filepath) > 100 * 1024:  # 100KB limit
            err_msg = (
                f"Error: File '{filepath}' is too large (> 100KB). "
                f"Please specify a smaller file or use other tools to process it."
            )
            ui.error(err_msg)
            return err_msg

        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            return content
    except FileNotFoundError:
        err_msg = f"Error: File not found at '{filepath}'."
        ui.error(err_msg)
        return err_msg
    except UnicodeDecodeError as e:
        err_msg = (
            f"Error reading file '{filepath}': Could not decode using UTF-8. "
            f"It might be a binary file or use a different encoding. {e}"
        )
        ui.error(err_msg)
        return err_msg
    except Exception as e:
        err_msg = f"Error reading file '{filepath}': {e}"
        ui.error(err_msg)
        return err_msg
