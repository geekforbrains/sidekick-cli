"""Tests for error handling integration in the REPL."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai.exceptions import ModelHTTPError

from sidekick.repl import Repl


@pytest.fixture
def mock_repl():
    """Fixture to create a mock Repl instance for testing."""
    with patch("sidekick.repl.get_or_create_agent"), patch("sidekick.repl._setup_signal_handler"):
        repl = Repl()
        repl.mcp_agent = MagicMock()
        return repl


@pytest.mark.asyncio
async def test_handle_user_request_with_error(mock_repl):
    """Test that _handle_user_request properly calls the error handler."""
    mock_ui = MagicMock()
    mock_session = MagicMock(sigint_received=False, current_task=None)

    with patch("sidekick.repl.process_request") as mock_process:
        mock_process.side_effect = ValueError("Test error")

        with patch("sidekick.repl.ui", mock_ui), patch("sidekick.repl.session", mock_session):
            await mock_repl._handle_user_request("test input")

            mock_ui.stop_spinner.assert_called()
            mock_ui.display_error_panel.assert_called_once()
            call_args = mock_ui.display_error_panel.call_args
            assert "ValueError" in call_args[0][0]
            assert "Test error" in call_args[0][0]
            assert "detail" in call_args[1]
            assert "Error log:" in call_args[1]["detail"]


@pytest.mark.asyncio
async def test_handle_user_request_with_model_http_error(mock_repl):
    """Test that ModelHTTPError doesn't create a log file."""
    mock_ui = MagicMock()
    mock_session = MagicMock(sigint_received=False, current_task=None)

    with patch("sidekick.repl.process_request") as mock_process:
        error = ModelHTTPError(
            status_code=400, model_name="test-model", body={"error": {"message": "Bad request"}}
        )
        mock_process.side_effect = error

        with patch("sidekick.repl.ui", mock_ui), patch("sidekick.repl.session", mock_session):
            await mock_repl._handle_user_request("test input")

            mock_ui.display_error_panel.assert_called_once_with("test-model: Bad request")


@pytest.mark.asyncio
async def test_handle_user_request_success(mock_repl):
    """Test that a successful request doesn't trigger error handling."""
    mock_ui = MagicMock()
    mock_session = MagicMock(sigint_received=False, current_task=None, last_usage=None)

    with patch("sidekick.repl.process_request") as mock_process:
        mock_process.return_value = "Success response"

        with patch("sidekick.repl.ui", mock_ui), patch("sidekick.repl.session", mock_session):
            await mock_repl._handle_user_request("test input")

            mock_ui.display_error_panel.assert_not_called()
            mock_ui.agent.assert_called_once_with("Success response", has_footer=False)


@pytest.mark.asyncio
async def test_handle_user_request_cancellation(mock_repl):
    """Test that cancellation is handled gracefully without error logging."""
    mock_ui = MagicMock()
    mock_session = MagicMock(
        sigint_received=False,
        current_task=None,
        agents={"test-model": MagicMock()},
        current_model="test-model",
    )

    with patch("sidekick.repl.process_request") as mock_process:
        mock_process.side_effect = asyncio.CancelledError()

        with patch("sidekick.repl.ui", mock_ui), patch("sidekick.repl.session", mock_session):
            mock_repl.mcp_agent._mcp_entered = False
            await mock_repl._handle_user_request("test input")

            mock_ui.warning.assert_called_once_with("Request cancelled")
            mock_ui.display_error_panel.assert_not_called()
