"""
Tool handling business logic, separated from UI concerns.
"""

from typing import TYPE_CHECKING

from sidekick.types import (SessionState, ToolArgs, ToolConfirmationRequest,
                            ToolConfirmationResponse, ToolName)

if TYPE_CHECKING:
    from pydantic_ai import Tool


class ToolHandler:
    """Handles tool confirmation logic separate from UI."""

    def __init__(self, session: SessionState):
        self.session = session

    def should_confirm(self, tool_name: ToolName) -> bool:
        """
        Determine if a tool requires confirmation.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            bool: True if confirmation is required, False otherwise.
        """
        return not (self.session.yolo or tool_name in self.session.tool_ignore)

    def process_confirmation(self, response: ToolConfirmationResponse, tool_name: ToolName) -> bool:
        """
        Process the confirmation response.

        Args:
            response: The confirmation response from the user.
            tool_name: Name of the tool being confirmed.

        Returns:
            bool: True if tool should proceed, False if aborted.
        """
        if response.skip_future:
            self.session.tool_ignore.append(tool_name)

        return response.approved and not response.abort

    def create_confirmation_request(
        self, tool_name: ToolName, args: ToolArgs
    ) -> ToolConfirmationRequest:
        """
        Create a confirmation request from tool information.

        Args:
            tool_name: Name of the tool.
            args: Tool arguments.

        Returns:
            ToolConfirmationRequest: The confirmation request.
        """
        filepath = args.get("filepath")
        return ToolConfirmationRequest(tool_name=tool_name, args=args, filepath=filepath)


def create_tools_with_config(tool_functions: list, max_retries: int) -> list["Tool"]:
    """
    Create Tool instances with standardized configuration.

    Args:
        tool_functions: List of tool functions to wrap.
        max_retries: Maximum number of retries for each tool.

    Returns:
        List of configured Tool instances.
    """
    from pydantic_ai import Tool

    return [Tool(tool, max_retries=max_retries) for tool in tool_functions]
