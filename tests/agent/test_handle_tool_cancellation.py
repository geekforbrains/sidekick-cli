"""Tests for *agent._handle_tool_cancellation* – rewritten to use shared helpers."""

from unittest.mock import MagicMock

import pytest
from pydantic_ai import messages

from sidekick.agent import _handle_tool_cancellation


@pytest.mark.asyncio
async def test_handle_tool_cancellation(monkeypatch, make_tool_call):
    # Prepare three tool calls
    calls = [make_tool_call(f"tool_{i}", f"id_{i}") for i in range(3)]

    # Patch session.messages once
    mock_messages = MagicMock()
    monkeypatch.setattr("sidekick.agent.session", MagicMock(messages=mock_messages))

    # Call with all three → expect one model request containing 3 parts
    await _handle_tool_cancellation(calls)

    mock_messages.append.assert_called_once()
    model_req = mock_messages.append.call_args[0][0]
    assert isinstance(model_req, messages.ModelRequest)
    assert [p.tool_name for p in model_req.parts] == [c.tool_name for c in calls]


@pytest.mark.asyncio
async def test_handle_tool_cancellation_empty(monkeypatch):
    mock_messages = MagicMock()
    monkeypatch.setattr("sidekick.agent.session", MagicMock(messages=mock_messages))

    await _handle_tool_cancellation([])
    mock_messages.append.assert_not_called()
