import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pydantic_ai import messages

from sidekick.agent import _process_node


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
async def test_process_node_with_tool_call_success():
    """Test processing a node with successful tool call."""
    # Create a mock node with tool call
    node = Mock()
    delattr(node, "request")

    tool_call = Mock(spec=messages.ToolCallPart)
    tool_call.part_kind = "tool-call"
    tool_call.tool_name = "test_tool"
    tool_call.tool_call_id = "test_123"

    node.model_response = Mock(spec=messages.ModelResponse)
    node.model_response.parts = [tool_call]

    # Mock session and _render_tool_call
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages

        with patch("sidekick.agent._render_tool_call", new_callable=AsyncMock) as mock_render:
            await _process_node(node)

            # Verify response was appended
            mock_messages.append.assert_called_once_with(node.model_response)

            # Verify tool call was rendered
            mock_render.assert_called_once_with(tool_call)


@pytest.mark.asyncio
async def test_process_node_with_tool_call_cancellation():
    """Test processing a node when tool call is cancelled."""
    # Create a mock node with tool call
    node = Mock()
    delattr(node, "request")

    tool_call = Mock(spec=messages.ToolCallPart)
    tool_call.part_kind = "tool-call"
    tool_call.tool_name = "test_tool"
    tool_call.tool_call_id = "test_123"

    node.model_response = Mock(spec=messages.ModelResponse)
    node.model_response.parts = [tool_call]

    # Mock session and _render_tool_call to raise CancelledError
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages

        with patch("sidekick.agent._render_tool_call", new_callable=AsyncMock) as mock_render:
            mock_render.side_effect = asyncio.CancelledError("Tool execution cancelled by user")

            with patch(
                "sidekick.agent._handle_tool_cancellation", new_callable=AsyncMock
            ) as mock_handle:
                # Verify the CancelledError is re-raised
                with pytest.raises(asyncio.CancelledError):
                    await _process_node(node)

                # Verify response was appended before cancellation
                assert mock_messages.append.call_count == 1
                mock_messages.append.assert_any_call(node.model_response)

                # Verify tool cancellation handler was called
                mock_handle.assert_called_once_with([tool_call])


@pytest.mark.asyncio
async def test_process_node_with_multiple_tool_calls_cancellation():
    """Test processing a node with multiple tool calls when one is cancelled."""
    # Create a mock node with multiple tool calls
    node = Mock()
    delattr(node, "request")

    tool_calls = []
    for i in range(3):
        tool_call = Mock(spec=messages.ToolCallPart)
        tool_call.part_kind = "tool-call"
        tool_call.tool_name = f"tool_{i}"
        tool_call.tool_call_id = f"id_{i}"
        tool_calls.append(tool_call)

    # Add a non-tool part to verify it's skipped
    text_part = Mock(spec=messages.TextPart)
    text_part.part_kind = "text"

    node.model_response = Mock(spec=messages.ModelResponse)
    node.model_response.parts = [tool_calls[0], text_part, tool_calls[1], tool_calls[2]]

    # Mock session and _render_tool_call to raise CancelledError on second tool
    with patch("sidekick.agent.session") as mock_session:
        mock_messages = MagicMock()
        mock_session.messages = mock_messages

        with patch("sidekick.agent._render_tool_call", new_callable=AsyncMock) as mock_render:
            # Succeed for first call, cancel on second
            mock_render.side_effect = [
                None,
                asyncio.CancelledError("Tool execution cancelled by user"),
            ]

            with patch(
                "sidekick.agent._handle_tool_cancellation", new_callable=AsyncMock
            ) as mock_handle:
                # Verify the CancelledError is re-raised
                with pytest.raises(asyncio.CancelledError):
                    await _process_node(node)

                # Verify only the first two tools were processed (before cancellation)
                assert mock_render.call_count == 2

                # Verify cancellation handler was called with ALL tool calls from the response
                mock_handle.assert_called_once_with([tool_calls[0], tool_calls[1], tool_calls[2]])
