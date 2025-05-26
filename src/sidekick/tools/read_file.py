"""
Module: sidekick.tools.read_file

File reading tool for agent operations in the Sidekick application.
Provides safe file reading with size limits and proper error handling.
"""

import os

from sidekick.constants import (ERROR_FILE_DECODE, ERROR_FILE_DECODE_DETAILS, ERROR_FILE_NOT_FOUND,
                                ERROR_FILE_TOO_LARGE, MAX_FILE_SIZE, MSG_FILE_SIZE_LIMIT)
from sidekick.types import FilePath, ToolResult
from sidekick.ui.output import info
from sidekick.ui.panels import error


async def read_file(filepath: FilePath) -> ToolResult:
    """
    Read the contents of a file.

    Args:
        filepath (FilePath): The path to the file to read.

    Returns:
        ToolResult: The contents of the file or an error message.
    """
    try:
        await info(f"Read({repr(filepath)})")

        # Add a size limit to prevent reading huge files
        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            err_msg = ERROR_FILE_TOO_LARGE.format(filepath=filepath) + MSG_FILE_SIZE_LIMIT
            await error(err_msg)
            return err_msg

        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            return content

    except FileNotFoundError:
        err_msg = ERROR_FILE_NOT_FOUND.format(filepath=filepath)
        await error(err_msg)
        return err_msg
    except UnicodeDecodeError as decode_error:
        err_msg = (
            ERROR_FILE_DECODE.format(filepath=filepath)
            + " "
            + ERROR_FILE_DECODE_DETAILS.format(error=decode_error)
        )
        await error(err_msg)
        return err_msg
    except Exception as read_error:
        err_msg = f"Error reading file '{filepath}': {read_error}"
        await error(err_msg)
        return err_msg
