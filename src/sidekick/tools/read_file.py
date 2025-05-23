"""
Module: sidekick.tools.read_file

File reading tool for agent operations in the Sidekick application.
Provides safe file reading with size limits and proper error handling.
"""

import os

from sidekick.constants import (ERROR_FILE_DECODE, ERROR_FILE_DECODE_DETAILS, ERROR_FILE_NOT_FOUND,
                                ERROR_FILE_TOO_LARGE, MAX_FILE_SIZE, MSG_FILE_SIZE_LIMIT)
from sidekick.exceptions import ToolExecutionError
from sidekick.tools.base import FileBasedTool
from sidekick.types import FilePath, ToolResult
from sidekick.ui import console as default_ui


class ReadFileTool(FileBasedTool):
    """Tool for reading file contents."""

    @property
    def tool_name(self) -> str:
        return "Read"

    async def _execute(self, filepath: FilePath) -> ToolResult:
        """Read the contents of a file.

        Args:
            filepath: The path to the file to read.

        Returns:
            ToolResult: The contents of the file or an error message.

        Raises:
            Exception: Any file reading errors
        """
        # Add a size limit to prevent reading huge files
        if os.path.getsize(filepath) > MAX_FILE_SIZE:
            err_msg = ERROR_FILE_TOO_LARGE.format(filepath=filepath) + MSG_FILE_SIZE_LIMIT
            if self.ui:
                await self.ui.error(err_msg)
            raise ToolExecutionError(tool_name=self.tool_name, message=err_msg, original_error=None)

        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            return content

    async def _handle_error(self, error: Exception, filepath: FilePath = None) -> ToolResult:
        """Handle errors with specific messages for common cases.

        Raises:
            ToolExecutionError: Always raised with structured error information
        """
        if isinstance(error, FileNotFoundError):
            err_msg = ERROR_FILE_NOT_FOUND.format(filepath=filepath)
        elif isinstance(error, UnicodeDecodeError):
            err_msg = (
                ERROR_FILE_DECODE.format(filepath=filepath)
                + " "
                + ERROR_FILE_DECODE_DETAILS.format(error=error)
            )
        else:
            # Use parent class handling for other errors
            await super()._handle_error(error, filepath)
            return  # super() will raise, this is unreachable

        if self.ui:
            await self.ui.error(err_msg)

        raise ToolExecutionError(tool_name=self.tool_name, message=err_msg, original_error=error)


# Create the function that maintains the existing interface
async def read_file(filepath: FilePath) -> ToolResult:
    """
    Read the contents of a file.

    Args:
        filepath (FilePath): The path to the file to read.

    Returns:
        ToolResult: The contents of the file or an error message.
    """
    tool = ReadFileTool(default_ui)
    try:
        return await tool.execute(filepath)
    except ToolExecutionError as e:
        # Return error message for pydantic-ai compatibility
        return str(e)
