from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic_ai import messages

from sidekick.agent import _handle_tool_cancellation


@pytest.mark.asyncio
async def test_handle_tool_cancellation_single_tool():
    """Test handling cancellation of a single tool call."""
    # Create a mock tool call
    tool_call = Mock(spec=messages.ToolCallPart)
    tool_call.tool_name = "test_tool"
    tool_call.tool_call_id = "test_123"

    # Mock session
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages

        # Call the handler
        await _handle_tool_cancellation([tool_call])

        # Verify a ModelRequest was appended with the cancellation
        assert mock_messages.append.call_count == 1
        appended_msg = mock_messages.append.call_args[0][0]

        assert isinstance(appended_msg, messages.ModelRequest)
        assert len(appended_msg.parts) == 1

        part = appended_msg.parts[0]
        assert isinstance(part, messages.ToolReturnPart)
        assert part.tool_name == "test_tool"
        assert part.tool_call_id == "test_123"
        assert part.content == "Tool execution cancelled by user"


@pytest.mark.asyncio
async def test_handle_tool_cancellation_multiple_tools():
    """Test handling cancellation of multiple tool calls."""
    # Create multiple mock tool calls
    tool_calls = []
    for i in range(3):
        tool_call = Mock(spec=messages.ToolCallPart)
        tool_call.tool_name = f"tool_{i}"
        tool_call.tool_call_id = f"id_{i}"
        tool_calls.append(tool_call)

    # Mock session
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages

        # Call the handler
        await _handle_tool_cancellation(tool_calls)

        # Verify a ModelRequest was appended
        assert mock_messages.append.call_count == 1
        appended_msg = mock_messages.append.call_args[0][0]

        assert isinstance(appended_msg, messages.ModelRequest)
        assert len(appended_msg.parts) == 3

        # Verify each tool got a cancellation result
        for i, part in enumerate(appended_msg.parts):
            assert isinstance(part, messages.ToolReturnPart)
            assert part.tool_name == f"tool_{i}"
            assert part.tool_call_id == f"id_{i}"
            assert part.content == "Tool execution cancelled by user"


@pytest.mark.asyncio
async def test_handle_tool_cancellation_empty_list():
    """Test handling cancellation with no tool calls."""
    # Mock session
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages

        # Call the handler with empty list
        await _handle_tool_cancellation([])

        # Verify no message was appended
        mock_messages.append.assert_not_called()
