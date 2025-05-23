"""Base tool class for all Sidekick tools.

This module provides a base class that implements common patterns
for all tools including error handling, UI logging, and ModelRetry support.
"""

from abc import ABC, abstractmethod

from pydantic_ai.exceptions import ModelRetry


class BaseTool(ABC):
    """Base class for all Sidekick tools providing common functionality."""

    def __init__(self, ui_logger=None):
        """Initialize the base tool.

        Args:
            ui_logger: UI logger instance for displaying messages
        """
        self.ui = ui_logger

    async def execute(self, *args, **kwargs) -> str:
        """Execute the tool with error handling and logging.

        This method wraps the tool-specific logic with:
        - UI logging of the operation
        - Exception handling (except ModelRetry)
        - Consistent error message formatting

        Returns:
            str: Success message or error message

        Raises:
            ModelRetry: Re-raised to guide the LLM
        """
        try:
            if self.ui:
                await self.ui.info(f"{self.tool_name}({self._format_args(*args, **kwargs)})")
            return await self._execute(*args, **kwargs)
        except ModelRetry as e:
            # Log as warning and re-raise for pydantic-ai
            if self.ui:
                await self.ui.warning(str(e))
            raise
        except Exception as e:
            return await self._handle_error(e, *args, **kwargs)

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the display name for this tool."""
        pass

    @abstractmethod
    async def _execute(self, *args, **kwargs) -> str:
        """Implement tool-specific logic here.

        This method should contain the core functionality of the tool.

        Returns:
            str: Success message describing what was done

        Raises:
            ModelRetry: When the LLM needs guidance
            Exception: Any other errors will be caught and handled
        """
        pass

    async def _handle_error(self, error: Exception, *args, **kwargs) -> str:
        """Handle errors in a consistent way.

        Args:
            error: The exception that was raised
            *args, **kwargs: Original arguments for context

        Returns:
            str: Error message formatted consistently
        """
        err_msg = f"Error {self._get_error_context(*args, **kwargs)}: {error}"
        if self.ui:
            await self.ui.error(err_msg)
        return err_msg

    def _format_args(self, *args, **kwargs) -> str:
        """Format arguments for display in UI logging.

        Override this method to customize how arguments are displayed.

        Returns:
            str: Formatted argument string
        """
        # Collect all arguments
        all_args = []

        # Add positional arguments
        for arg in args:
            if isinstance(arg, str) and len(arg) > 50:
                # Truncate long strings
                all_args.append(f"'{arg[:47]}...'")
            else:
                all_args.append(repr(arg))

        # Add keyword arguments
        for key, value in kwargs.items():
            if isinstance(value, str) and len(value) > 50:
                all_args.append(f"{key}='{value[:47]}...'")
            else:
                all_args.append(f"{key}={repr(value)}")

        return ", ".join(all_args)

    def _get_error_context(self, *args, **kwargs) -> str:
        """Get context string for error messages.

        Override this method to provide tool-specific error context.

        Returns:
            str: Context for the error message
        """
        return f"in {self.tool_name}"


class FileBasedTool(BaseTool):
    """Base class for tools that work with files.

    Provides common file-related functionality like:
    - Path validation
    - File existence checking
    - Directory creation
    - Encoding handling
    """

    def _format_args(self, filepath: str, *args, **kwargs) -> str:
        """Format arguments with filepath as first argument."""
        # Always show the filepath first
        all_args = [repr(filepath)]

        # Add remaining positional arguments
        for arg in args:
            if isinstance(arg, str) and len(arg) > 50:
                all_args.append(f"'{arg[:47]}...'")
            else:
                all_args.append(repr(arg))

        # Add keyword arguments
        for key, value in kwargs.items():
            if isinstance(value, str) and len(value) > 50:
                all_args.append(f"{key}='{value[:47]}...'")
            else:
                all_args.append(f"{key}={repr(value)}")

        return ", ".join(all_args)

    def _get_error_context(self, filepath: str = None, *args, **kwargs) -> str:
        """Get error context including file path."""
        if filepath:
            return f"handling file '{filepath}'"
        return super()._get_error_context(*args, **kwargs)
