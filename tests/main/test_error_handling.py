"""Tests for error handling integration in main.py."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai.exceptions import ModelHTTPError

from sidekick.main import _handle_user_request


@pytest.mark.asyncio
async def test_handle_user_request_with_error():
    """Test that handle_user_request properly calls error handler."""
    mock_ui = MagicMock()
    mock_session = MagicMock()
    mock_session.sigint_received = False
    mock_session.current_task = None

    # Mock process_request to raise an error
    with patch("sidekick.main.process_request") as mock_process:
        mock_process.side_effect = ValueError("Test error")

        with patch("sidekick.main.ui", mock_ui), patch("sidekick.main.session", mock_session):

            mcp_agent = MagicMock()
            await _handle_user_request("test input", mcp_agent)

            # Verify spinner was stopped
            mock_ui.stop_spinner.assert_called()

            # Verify error was displayed
            mock_ui.display_error_panel.assert_called_once()
            call_args = mock_ui.display_error_panel.call_args
            assert "ValueError" in call_args[0][0]
            assert "Test error" in call_args[0][0]
            # Should have log file in detail
            assert "detail" in call_args[1]
            assert "Error log:" in call_args[1]["detail"]


@pytest.mark.asyncio
async def test_handle_user_request_with_model_http_error():
    """Test that ModelHTTPError doesn't create log file."""
    mock_ui = MagicMock()
    mock_session = MagicMock()
    mock_session.sigint_received = False
    mock_session.current_task = None

    with patch("sidekick.main.process_request") as mock_process:
        error = ModelHTTPError(
            status_code=400, model_name="test-model", body={"error": {"message": "Bad request"}}
        )
        mock_process.side_effect = error

        with patch("sidekick.main.ui", mock_ui), patch("sidekick.main.session", mock_session):

            mcp_agent = MagicMock()
            await _handle_user_request("test input", mcp_agent)

            # Verify error was displayed without log file
            mock_ui.display_error_panel.assert_called_once_with("test-model: Bad request")


@pytest.mark.asyncio
async def test_handle_user_request_success():
    """Test successful request doesn't trigger error handling."""
    mock_ui = MagicMock()
    mock_session = MagicMock()
    mock_session.sigint_received = False
    mock_session.current_task = None
    mock_session.last_usage = None

    with patch("sidekick.main.process_request") as mock_process:
        mock_process.return_value = "Success response"

        with patch("sidekick.main.ui", mock_ui), patch("sidekick.main.session", mock_session):

            mcp_agent = MagicMock()
            await _handle_user_request("test input", mcp_agent)

            # Should not call error
            mock_ui.display_error_panel.assert_not_called()
            # Should display agent response
            mock_ui.agent.assert_called_once_with("Success response", has_footer=False)


@pytest.mark.asyncio
async def test_handle_user_request_cancellation():
    """Test that cancellation is handled without error logging."""
    mock_ui = MagicMock()
    mock_session = MagicMock()
    mock_session.sigint_received = False
    mock_session.current_task = None
    mock_session.agents = {"test-model": MagicMock()}
    mock_session.current_model = "test-model"

    with patch("sidekick.main.process_request") as mock_process:
        mock_process.side_effect = asyncio.CancelledError()

        with (
            patch("sidekick.main.ui", mock_ui),
            patch("sidekick.main.session", mock_session),
            patch("sidekick.main.get_or_create_agent") as mock_get_agent,
        ):

            mock_get_agent.return_value = MagicMock(_mcp_entered=False)
            mcp_agent = MagicMock(_mcp_entered=False)

            await _handle_user_request("test input", mcp_agent)

            # Should show warning, not error
            mock_ui.warning.assert_called_once_with("Request cancelled")
            mock_ui.display_error_panel.assert_not_called()
