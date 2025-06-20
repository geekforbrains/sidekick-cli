"""Tests for error handling in main.py."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai.exceptions import ModelHTTPError

from sidekick.main import handle_user_request


@pytest.mark.asyncio
async def test_handle_model_http_error_with_dict_body():
    """Test handling ModelHTTPError with dictionary body containing error message."""
    # Mock UI functions
    with patch("sidekick.main.ui") as mock_ui:
        # Mock process_request to raise ModelHTTPError
        with patch("sidekick.main.process_request") as mock_process:
            error_body = {
                "error": {"message": "Your credit balance is too low to access the Anthropic API."}
            }
            mock_process.side_effect = ModelHTTPError(
                status_code=400, model_name="claude-3-5-sonnet", body=error_body
            )

            # Mock session
            mock_session = MagicMock()
            mock_session.sigint_received = False
            mock_session.current_task = None

            with patch("sidekick.main.session", mock_session):
                # Call handle_user_request
                mcp_agent = MagicMock()
                await handle_user_request("test input", mcp_agent)

                # Verify error was displayed correctly
                mock_ui.error.assert_called_once_with(
                    "claude-3-5-sonnet: Your credit balance is too low to access the Anthropic API."
                )
                mock_ui.stop_spinner.assert_called()


@pytest.mark.asyncio
async def test_handle_model_http_error_with_message_in_body():
    """Test handling ModelHTTPError with message directly in body."""
    with patch("sidekick.main.ui") as mock_ui:
        with patch("sidekick.main.process_request") as mock_process:
            error_body = {"message": "API rate limit exceeded"}
            mock_process.side_effect = ModelHTTPError(
                status_code=429, model_name="gpt-4", body=error_body
            )

            mock_session = MagicMock()
            mock_session.sigint_received = False
            mock_session.current_task = None

            with patch("sidekick.main.session", mock_session):
                mcp_agent = MagicMock()
                await handle_user_request("test input", mcp_agent)

                mock_ui.error.assert_called_once_with("gpt-4: API rate limit exceeded")
                mock_ui.stop_spinner.assert_called()


@pytest.mark.asyncio
async def test_handle_model_http_error_fallback_to_string():
    """Test handling ModelHTTPError when body doesn't contain expected message structure."""
    with patch("sidekick.main.ui") as mock_ui:
        with patch("sidekick.main.process_request") as mock_process:
            # Body without standard error structure
            error_body = {"some_field": "some_value"}
            mock_process.side_effect = ModelHTTPError(
                status_code=500, model_name="gemini", body=error_body
            )

            mock_session = MagicMock()
            mock_session.sigint_received = False
            mock_session.current_task = None

            with patch("sidekick.main.session", mock_session):
                mcp_agent = MagicMock()
                await handle_user_request("test input", mcp_agent)

                # Should fallback to string representation
                mock_ui.error.assert_called_once()
                error_call_args = mock_ui.error.call_args[0][0]
                assert "gemini:" in error_call_args
                assert "500" in error_call_args
                mock_ui.stop_spinner.assert_called()


@pytest.mark.asyncio
async def test_handle_generic_exception_still_shows_traceback():
    """Test that non-ModelHTTPError exceptions still show full traceback."""
    with patch("sidekick.main.ui") as mock_ui:
        with patch("sidekick.main.process_request") as mock_process:
            # Raise a different type of exception
            mock_process.side_effect = ValueError("Something went wrong")

            mock_session = MagicMock()
            mock_session.sigint_received = False
            mock_session.current_task = None

            with patch("sidekick.main.session", mock_session):
                mcp_agent = MagicMock()
                await handle_user_request("test input", mcp_agent)

                # Should show full error with traceback
                mock_ui.error.assert_called_once()
                error_call = mock_ui.error.call_args
                assert "Something went wrong" in str(error_call[0][0])
                # Check that detail (traceback) was provided
                assert "detail" in error_call[1]
                assert error_call[1]["detail"] is not None
                mock_ui.stop_spinner.assert_called()


@pytest.mark.asyncio
async def test_successful_request_no_error():
    """Test that successful requests don't trigger error handling."""
    with patch("sidekick.main.ui") as mock_ui:
        with patch("sidekick.main.process_request") as mock_process:
            # Successful response
            mock_process.return_value = "Success response"

            mock_session = MagicMock()
            mock_session.sigint_received = False
            mock_session.current_task = None
            mock_session.last_usage = None

            with patch("sidekick.main.session", mock_session):
                mcp_agent = MagicMock()
                await handle_user_request("test input", mcp_agent)

                # Should not call error
                mock_ui.error.assert_not_called()
                # Should display agent response
                mock_ui.agent.assert_called_once_with("Success response")
                mock_ui.stop_spinner.assert_called()


@pytest.mark.asyncio
async def test_handle_google_client_error():
    """Test handling Google ClientError that escapes pydantic_ai wrapping."""
    with patch("sidekick.main.ui") as mock_ui:
        with patch("sidekick.main.process_request") as mock_process:
            # Create a mock Google ClientError
            class MockGoogleClientError(Exception):
                def __init__(self):
                    self.details = {
                        "error": {
                            "code": 400,
                            "message": "API key not valid. Please pass a valid API key.",
                            "status": "INVALID_ARGUMENT",
                        }
                    }
                    super().__init__("400 INVALID_ARGUMENT. " + str(self.details))

            mock_error = MockGoogleClientError()
            mock_error.__class__.__module__ = "google.genai.errors"
            mock_error.__class__.__name__ = "ClientError"

            mock_process.side_effect = mock_error

            mock_session = MagicMock()
            mock_session.sigint_received = False
            mock_session.current_task = None

            with patch("sidekick.main.session", mock_session):
                mcp_agent = MagicMock()
                await handle_user_request("test input", mcp_agent)

                # Should extract and display clean error message
                mock_ui.error.assert_called_once_with(
                    "Google: API key not valid. Please pass a valid API key."
                )
                mock_ui.stop_spinner.assert_called()


@pytest.mark.asyncio
async def test_handle_openai_api_status_error():
    """Test handling OpenAI APIStatusError that escapes pydantic_ai wrapping."""
    with patch("sidekick.main.ui") as mock_ui:
        with patch("sidekick.main.process_request") as mock_process:
            # Create a mock OpenAI APIStatusError
            class MockOpenAIAPIStatusError(Exception):
                def __init__(self):
                    self.body = {
                        "error": {
                            "message": (
                                "You exceeded your current quota, "
                                "please check your plan and billing details."
                            ),
                            "type": "insufficient_quota",
                            "code": "insufficient_quota",
                        }
                    }
                    super().__init__("OpenAI API error")

            mock_error = MockOpenAIAPIStatusError()
            mock_error.__class__.__module__ = "openai"
            mock_error.__class__.__name__ = "APIStatusError"

            mock_process.side_effect = mock_error

            mock_session = MagicMock()
            mock_session.sigint_received = False
            mock_session.current_task = None

            with patch("sidekick.main.session", mock_session):
                mcp_agent = MagicMock()
                await handle_user_request("test input", mcp_agent)

                # Should extract and display clean error message
                mock_ui.error.assert_called_once_with(
                    "OpenAI: You exceeded your current quota, "
                    "please check your plan and billing details."
                )
                mock_ui.stop_spinner.assert_called()


@pytest.mark.asyncio
async def test_handle_anthropic_authentication_error():
    """Test handling Anthropic AuthenticationError that escapes pydantic_ai wrapping."""
    with patch("sidekick.main.ui") as mock_ui:
        with patch("sidekick.main.process_request") as mock_process:
            # Create a mock Anthropic AuthenticationError
            class MockAnthropicAuthError(Exception):
                def __init__(self):
                    self.message = "Invalid API key provided"
                    super().__init__(self.message)

            mock_error = MockAnthropicAuthError()
            mock_error.__class__.__module__ = "anthropic"
            mock_error.__class__.__name__ = "AuthenticationError"

            mock_process.side_effect = mock_error

            mock_session = MagicMock()
            mock_session.sigint_received = False
            mock_session.current_task = None

            with patch("sidekick.main.session", mock_session):
                mcp_agent = MagicMock()
                await handle_user_request("test input", mcp_agent)

                # Should extract and display clean error message
                mock_ui.error.assert_called_once_with("Anthropic: Invalid API key provided")
                mock_ui.stop_spinner.assert_called()
