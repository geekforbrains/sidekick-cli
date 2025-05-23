"""
Tool handling business logic, separated from UI concerns.
"""

from sidekick.core.state import StateManager
from sidekick.types import ToolArgs, ToolConfirmationRequest, ToolConfirmationResponse, ToolName


class ToolHandler:
    """Handles tool confirmation logic separate from UI."""

    def __init__(self, state_manager: StateManager):
        self.state = state_manager

    def should_confirm(self, tool_name: ToolName) -> bool:
        """
        Determine if a tool requires confirmation.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            bool: True if confirmation is required, False otherwise.
        """
        return not (self.state.session.yolo or tool_name in self.state.session.tool_ignore)

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
            self.state.session.tool_ignore.append(tool_name)

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
