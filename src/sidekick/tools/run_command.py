import subprocess

from sidekick.tools.base import BaseTool
from sidekick.types import ToolResult
from sidekick.ui import console as ui


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
        output = stdout.strip() or "No output."
        error = stderr.strip() or "No errors."
        resp = f"STDOUT:\n{output}\n\nSTDERR:\n{error}".strip()

        # Truncate if the output is too long to prevent issues
        if len(resp) > 5000:
            # Include both the beginning and end of the output
            start_part = resp[:2500]
            end_part = resp[-1000:] if len(resp) > 3500 else resp[2500:]
            truncated_resp = start_part + "\n...\n[truncated]\n...\n" + end_part
            return truncated_resp

        return resp

    async def _handle_error(self, error: Exception, command: str = None) -> ToolResult:
        """Handle errors with specific messages for common cases."""
        if isinstance(error, FileNotFoundError):
            err_msg = f"Error: Command not found or failed to execute: {command}. Details: {error}"
        else:
            # Use parent class handling for other errors
            return await super()._handle_error(error, command)

        if self.ui:
            await self.ui.error(err_msg)
        return err_msg

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
    tool = RunCommandTool(ui)
    return await tool.execute(command)
