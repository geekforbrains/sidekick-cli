"""
Module: sidekick.tools.run_command

Command execution tool for agent operations in the Sidekick application.
Provides controlled shell command execution with output capture and truncation.
"""

import subprocess

from sidekick.constants import (CMD_OUTPUT_FORMAT, CMD_OUTPUT_NO_ERRORS, CMD_OUTPUT_NO_OUTPUT,
                                CMD_OUTPUT_TRUNCATED, COMMAND_OUTPUT_END_SIZE,
                                COMMAND_OUTPUT_START_INDEX, COMMAND_OUTPUT_THRESHOLD,
                                ERROR_COMMAND_EXECUTION, MAX_COMMAND_OUTPUT)
from sidekick.exceptions import ToolExecutionError
from sidekick.tools.base import BaseTool
from sidekick.types import ToolResult
from sidekick.ui import console as default_ui


class RunCommandTool(BaseTool):
    """Tool for running shell commands."""

    @property
    def tool_name(self) -> str:
        return "Shell"

    async def _execute(self, command: str) -> ToolResult:
        """Run a shell command and return the output.

        Args:
            command: The command to run.

        Returns:
            ToolResult: The output of the command (stdout and stderr).

        Raises:
            FileNotFoundError: If command not found
            Exception: Any command execution errors
        """
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        output = stdout.strip() or CMD_OUTPUT_NO_OUTPUT
        error = stderr.strip() or CMD_OUTPUT_NO_ERRORS
        resp = CMD_OUTPUT_FORMAT.format(output=output, error=error).strip()

        # Truncate if the output is too long to prevent issues
        if len(resp) > MAX_COMMAND_OUTPUT:
            # Include both the beginning and end of the output
            start_part = resp[:COMMAND_OUTPUT_START_INDEX]
            end_part = (
                resp[-COMMAND_OUTPUT_END_SIZE:]
                if len(resp) > COMMAND_OUTPUT_THRESHOLD
                else resp[COMMAND_OUTPUT_START_INDEX:]
            )
            truncated_resp = start_part + CMD_OUTPUT_TRUNCATED + end_part
            return truncated_resp

        return resp

    async def _handle_error(self, error: Exception, command: str = None) -> ToolResult:
        """Handle errors with specific messages for common cases.

        Raises:
            ToolExecutionError: Always raised with structured error information
        """
        if isinstance(error, FileNotFoundError):
            err_msg = ERROR_COMMAND_EXECUTION.format(command=command, error=error)
        else:
            # Use parent class handling for other errors
            await super()._handle_error(error, command)
            return  # super() will raise, this is unreachable

        if self.ui:
            await self.ui.error(err_msg)

        raise ToolExecutionError(tool_name=self.tool_name, message=err_msg, original_error=error)

    def _get_error_context(self, command: str = None) -> str:
        """Get error context for command execution."""
        if command:
            return f"running command '{command}'"
        return super()._get_error_context()


# Create the function that maintains the existing interface
async def run_command(command: str) -> ToolResult:
    """
    Run a shell command and return the output. User must confirm risky commands.

    Args:
        command (str): The command to run.

    Returns:
        ToolResult: The output of the command (stdout and stderr) or an error message.
    """
    tool = RunCommandTool(default_ui)
    try:
        return await tool.execute(command)
    except ToolExecutionError as e:
        # Return error message for pydantic-ai compatibility
        return str(e)
