from unittest.mock import Mock, patch

import pytest
from pydantic_ai import messages

from sidekick.agent import _process_node


@pytest.mark.asyncio
async def test_process_node_with_request():
    """Test processing a node with a request."""
    node = Mock()
    node.request = Mock(spec=messages.ModelRequest)
    node.request.parts = []

    delattr(node, "model_response")

    mock_message_history = Mock()

    await _process_node(node, mock_message_history)

    mock_message_history.add_request.assert_called_once_with(node.request)


@pytest.mark.asyncio
async def test_process_node_with_model_response_no_tools():
    """Test processing a node with model response but no tool calls."""
    node = Mock()
    delattr(node, "request")

    text_part = Mock(spec=messages.TextPart)
    text_part.part_kind = "text"

    node.model_response = Mock(spec=messages.ModelResponse)
    node.model_response.parts = [text_part]

    mock_message_history = Mock()

    await _process_node(node, mock_message_history)

    mock_message_history.add_response.assert_called_once_with(node.model_response)


@pytest.mark.asyncio
async def test_process_node_with_tool_call():
    """Test processing a node with tool call."""
    node = Mock()
    delattr(node, "request")

    tool_call = Mock(spec=messages.ToolCallPart)
    tool_call.part_kind = "tool-call"
    tool_call.tool_name = "test_tool"
    tool_call.tool_call_id = "test_123"
    tool_call.args_as_dict = Mock(return_value={"arg1": "value1"})

    node.model_response = Mock(spec=messages.ModelResponse)
    node.model_response.parts = [tool_call]

    mock_message_history = Mock()

    await _process_node(node, mock_message_history)

    mock_message_history.add_response.assert_called_once_with(node.model_response)


@pytest.mark.asyncio
async def test_process_node_with_tool_return():
    """Test processing a node with tool return."""
    node = Mock()
    delattr(node, "model_response")

    tool_return = Mock()
    tool_return.part_kind = "tool-return"
    tool_return.tool_call_id = "test_123"

    node.request = Mock(spec=messages.ModelRequest)
    node.request.parts = [tool_return]

    mock_message_history = Mock()

    await _process_node(node, mock_message_history)

    mock_message_history.add_request.assert_called_once_with(node.request)


@pytest.mark.asyncio
async def test_process_node_with_retry_prompt():
    """Test processing a node with retry prompt."""
    node = Mock()
    delattr(node, "model_response")

    retry_part = Mock()
    retry_part.part_kind = "retry-prompt"
    retry_part.content = "Trying a different approach"

    node.request = Mock(spec=messages.ModelRequest)
    node.request.parts = [retry_part]

    mock_message_history = Mock()

    with patch("sidekick.agent.ui.muted") as mock_muted:
        await _process_node(node, mock_message_history)

        mock_muted.assert_called_once_with("Trying a different approach")
