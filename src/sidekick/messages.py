"""Message history management for Sidekick sessions."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from pydantic_ai import messages

log = logging.getLogger(__name__)


@dataclass
class MessageHistory:
    """Manages conversation message history with support for future pruning."""

    _messages: List[messages.ModelMessage] = field(default_factory=list)
    _project_guide: Optional[str] = None

    def add_request(self, request: messages.ModelRequest) -> None:
        """Add a request message to the history."""
        self._messages.append(request)
        log.debug("Added request to message history")

    def add_response(self, response: messages.ModelResponse) -> None:
        """Add a model response to the history.

        This is where future pruning logic could be implemented to remove
        thinking parts and verbose tool outputs after the response is complete.
        """
        self._messages.append(response)
        log.debug("Added model response to message history")

    def patch_on_error(self, error_message: str) -> None:
        """Patch the message history with a ToolReturnPart on error.

        This is critical for maintaining valid message history when a tool call fails,
        the user interrupts execution, or other errors occur. LLM models expect to see
        both a tool call and its corresponding response in the history. Without this
        patch, the next request would fail because the model would see an unanswered
        tool call in the history.

        This method finds the last tool call in the most recent response and creates
        a synthetic tool return with the error message, ensuring the conversation
        history remains valid for future interactions.
        """
        if not self._messages:
            return

        last_message = self._messages[-1]

        if not (
            hasattr(last_message, "kind")
            and last_message.kind == "response"
            and hasattr(last_message, "parts")
        ):
            return

        last_tool_call = None
        for part in reversed(last_message.parts):
            if hasattr(part, "part_kind") and part.part_kind == "tool-call":
                last_tool_call = part
                break

        if last_tool_call:
            tool_return = messages.ToolReturnPart(
                tool_name=last_tool_call.tool_name,
                tool_call_id=last_tool_call.tool_call_id,
                content=error_message,
            )
            self.add_request(messages.ModelRequest(parts=[tool_return]))

    def clear(self) -> None:
        """Clear all messages from the history."""
        self._messages.clear()
        log.debug("Cleared message history")

    def get_messages(self) -> List[messages.ModelMessage]:
        """Get a copy of all messages for agent use."""
        return self._messages.copy()

    def get_messages_for_agent(self) -> List[messages.ModelMessage]:
        """Get messages for agent use, with project guide prepended if available."""
        messages_copy = self._messages.copy()

        if self._project_guide:
            guide_message = messages.ModelRequest(
                parts=[messages.UserPromptPart(content=self._project_guide)]
            )
            messages_copy.insert(0, guide_message)
            log.debug("Prepended project guide to message history")

        return messages_copy

    def set_project_guide(self, guide: Optional[str]) -> None:
        """Set the project guide content."""
        self._project_guide = guide

    def __len__(self) -> int:
        """Return the number of messages in history."""
        return len(self._messages)

    def __iter__(self):
        """Allow iteration over messages."""
        return iter(self._messages)

    def __getitem__(self, index):
        """Allow indexed access to messages."""
        return self._messages[index]
