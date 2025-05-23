import os

from sidekick.tools.base import FileBasedTool
from sidekick.ui import console as ui


class ReadFileTool(FileBasedTool):
    """Tool for reading file contents."""

    @property
    def tool_name(self) -> str:
        return "Read"

    async def _execute(self, filepath: str) -> str:
        """Read the contents of a file.

        Args:
            filepath: The path to the file to read.

        Returns:
            str: The contents of the file or an error message.

        Raises:
            Exception: Any file reading errors
        """
        # Add a size limit to prevent reading huge files
        if os.path.getsize(filepath) > 100 * 1024:  # 100KB limit
            err_msg = (
                f"Error: File '{filepath}' is too large (> 100KB). "
                f"Please specify a smaller file or use other tools to process it."
            )
            if self.ui:
                await self.ui.error(err_msg)
            return err_msg

        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            return content

    async def _handle_error(self, error: Exception, filepath: str = None) -> str:
        """Handle errors with specific messages for common cases."""
        if isinstance(error, FileNotFoundError):
            err_msg = f"Error: File not found at '{filepath}'."
        elif isinstance(error, UnicodeDecodeError):
            err_msg = (
                f"Error reading file '{filepath}': Could not decode using UTF-8. "
                f"It might be a binary file or use a different encoding. {error}"
            )
        else:
            # Use parent class handling for other errors
            return await super()._handle_error(error, filepath)

        if self.ui:
            await self.ui.error(err_msg)
        return err_msg


# Create the function that maintains the existing interface
async def read_file(filepath: str) -> str:
    """
    Read the contents of a file.

    Args:
        filepath (str): The path to the file to read.

    Returns:
        str: The contents of the file or an error message.
    """
    tool = ReadFileTool(ui)
    return await tool.execute(filepath)
