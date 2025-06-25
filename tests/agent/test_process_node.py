from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pydantic_ai import messages

from sidekick.agent import _process_node, _track_tool_request


@pytest.mark.asyncio
async def test_process_node_with_request():
    """Test processing a node with a request."""
    # Create a mock node with request
    node = Mock()
    node.request = Mock(spec=messages.ModelRequest)
    node.request.parts = []

    # Remove model_response attribute
    delattr(node, "model_response")

    # Mock session
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages

        await _process_node(node)

        # Verify request was appended
        mock_messages.append.assert_called_once_with(node.request)


@pytest.mark.asyncio
async def test_process_node_with_model_response_no_tools():
    """Test processing a node with model response but no tool calls."""
    # Create a mock node with model response
    node = Mock()
    delattr(node, "request")

    text_part = Mock(spec=messages.TextPart)
    text_part.part_kind = "text"

    node.model_response = Mock(spec=messages.ModelResponse)
    node.model_response.parts = [text_part]

    # Mock session
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages

        await _process_node(node)

        # Verify response was appended
        mock_messages.append.assert_called_once_with(node.model_response)


@pytest.mark.asyncio
async def test_process_node_with_tool_call_tracking():
    """Test processing a node with tool call gets tracked."""
    # Create a mock node with tool call
    node = Mock()
    delattr(node, "request")

    tool_call = Mock(spec=messages.ToolCallPart)
    tool_call.part_kind = "tool-call"
    tool_call.tool_name = "test_tool"
    tool_call.tool_call_id = "test_123"
    tool_call.args_as_dict = Mock(return_value={"arg1": "value1"})

    node.model_response = Mock(spec=messages.ModelResponse)
    node.model_response.parts = [tool_call]

    # Mock session and _track_tool_request
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages

        with patch("sidekick.agent._track_tool_request", new_callable=AsyncMock) as mock_track:
            await _process_node(node)

            # Verify response was appended
            mock_messages.append.assert_called_once_with(node.model_response)

            # Verify tool call was tracked
            mock_track.assert_called_once_with(tool_call)


@pytest.mark.asyncio
async def test_process_node_with_tool_return():
    """Test processing a node with tool return shows status."""
    # Create a mock node with tool return
    node = Mock()
    delattr(node, "model_response")

    tool_return = Mock()
    tool_return.part_kind = "tool-return"
    tool_return.tool_call_id = "test_123"

    node.request = Mock(spec=messages.ModelRequest)
    node.request.parts = [tool_return]

    # Mock session with pending tools
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages
        mock_session.pending_tools = {"test_123": {"name": "test_tool", "args": {"arg1": "value1"}}}
        mock_session.tool_usage = {}
        mock_session.spinner = None

        with patch("sidekick.agent._format_tool_display", new_callable=AsyncMock) as mock_display:
            await _process_node(node)

            # Verify request was appended
            mock_messages.append.assert_called_once_with(node.request)

            # Verify tool display was called
            mock_display.assert_called_once_with("test_tool", {"arg1": "value1"})

            # Verify tool usage was tracked
            assert mock_session.tool_usage["test_tool"] == 1

            # Verify pending tool was cleaned up
            assert "test_123" not in mock_session.pending_tools


@pytest.mark.asyncio
async def test_process_node_with_retry_prompt():
    """Test processing a node with retry prompt."""
    # Create a mock node with retry prompt
    node = Mock()
    delattr(node, "model_response")

    retry_part = Mock()
    retry_part.part_kind = "retry-prompt"
    retry_part.content = "Trying a different approach"

    node.request = Mock(spec=messages.ModelRequest)
    node.request.parts = [retry_part]

    # Mock session and ui
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages
        mock_session.spinner = None

        with patch("sidekick.agent.ui.muted") as mock_muted:
            await _process_node(node)

            # Verify retry message was displayed
            mock_muted.assert_called_once_with("Trying a different approach")


@pytest.mark.asyncio
async def test_track_tool_request():
    """Test tracking tool requests."""
    # Create a mock tool call
    tool_call = Mock()
    tool_call.tool_call_id = "test_123"
    tool_call.tool_name = "test_tool"
    tool_call.args_as_dict = Mock(return_value={"arg1": "value1"})

    # Mock session
    with patch("sidekick.agent.session") as mock_session:
        # Test when pending_tools doesn't exist
        delattr(mock_session, "pending_tools")

        await _track_tool_request(tool_call)

        # Verify pending_tools was created and tool was tracked
        assert hasattr(mock_session, "pending_tools")
        assert mock_session.pending_tools["test_123"] == {
            "name": "test_tool",
            "args": {"arg1": "value1"},
        }

        # Test when pending_tools already exists
        await _track_tool_request(tool_call)

        # Verify it still works
        assert mock_session.pending_tools["test_123"] == {
            "name": "test_tool",
            "args": {"arg1": "value1"},
        }
