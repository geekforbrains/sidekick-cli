"""
Tool handling business logic, separated from UI concerns.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sidekick.core.state import StateManager


@dataclass
class ToolConfirmationRequest:
    """Request for tool confirmation."""

    tool_name: str
    args: Dict[str, Any]
    filepath: Optional[str] = None


@dataclass
class ToolConfirmationResponse:
    """Response from tool confirmation."""

    approved: bool
    skip_future: bool = False
    abort: bool = False


class ToolHandler:
    """Handles tool confirmation logic separate from UI."""

    def __init__(self, state_manager: StateManager):
        self.state = state_manager

    def should_confirm(self, tool_name: str) -> bool:
        """
        Determine if a tool requires confirmation.

        Args:
            tool_name: Name of the tool to check.

        Returns:
            bool: True if confirmation is required, False otherwise.
        """
        return not (self.state.session.yolo or tool_name in self.state.session.tool_ignore)

    def process_confirmation(self, response: ToolConfirmationResponse, tool_name: str) -> bool:
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
        self, tool_name: str, args: Dict[str, Any]
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
