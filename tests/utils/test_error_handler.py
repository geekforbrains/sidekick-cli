"""Tests for error_handler utility."""

from unittest.mock import MagicMock

import pytest
from pydantic_ai.exceptions import ModelHTTPError

from sidekick.utils.error import (
    extract_error_message,
    handle_error,
    save_error_log,
    should_log_error,
)


def test_extract_error_message_model_http_error():
    """Test extracting message from ModelHTTPError."""
    error = ModelHTTPError(
        status_code=400,
        model_name="TestModel",
        body={"error": {"message": "Invalid API key"}},
    )

    result = extract_error_message(error)
    assert result == "TestModel: Invalid API key"


def test_extract_error_message_model_http_error_direct_message():
    """Test extracting message from ModelHTTPError with message in body."""
    error = ModelHTTPError(
        status_code=429,
        model_name="TestModel",
        body={"message": "Rate limit exceeded"},
    )

    result = extract_error_message(error)
    assert result == "TestModel: Rate limit exceeded"


def test_extract_error_message_malformed_function_call():
    """Test extracting message for MALFORMED_FUNCTION_CALL error."""
    error = Exception("Content field missing, MALFORMED_FUNCTION_CALL")

    result = extract_error_message(error)
    assert result == "The AI model had trouble executing a function. Please try again."


def test_extract_error_message_content_field_missing():
    """Test extracting message for Content field missing error."""
    error = Exception("Content field missing from response")

    result = extract_error_message(error)
    expected = (
        "The AI model returned an unexpected response format. This might be a temporary issue."
    )
    assert result == expected


def test_extract_error_message_long_error():
    """Test that long error messages are truncated."""
    long_message = "x" * 200
    error = Exception(long_message)

    result = extract_error_message(error)
    assert len(result) < 200
    assert result.endswith("...")
    assert "Exception" in result


def test_extract_error_message_provider_error_openai():
    """Test extracting message from OpenAI provider error."""

    class MockOpenAIError(Exception):
        def __init__(self):
            self.body = {"error": {"message": "Rate limit exceeded"}}
            super().__init__()

    error = MockOpenAIError()
    error.__class__.__name__ = "APIStatusError"
    error.__class__.__module__ = "openai"

    result = extract_error_message(error)
    assert result == "OpenAI: Rate limit exceeded"


def test_extract_error_message_provider_error_anthropic():
    """Test extracting message from Anthropic provider error."""

    class MockAnthropicError(Exception):
        def __init__(self):
            self.message = "Invalid API key"
            super().__init__()

    error = MockAnthropicError()
    error.__class__.__name__ = "AuthenticationError"
    error.__class__.__module__ = "anthropic"

    result = extract_error_message(error)
    assert result == "Anthropic: Invalid API key"


def test_extract_error_message_provider_error_google():
    """Test extracting message from Google provider error."""

    class MockGoogleError(Exception):
        def __init__(self):
            self.details = {"error": {"message": "API key not valid"}}
            super().__init__()

    error = MockGoogleError()
    error.__class__.__name__ = "ClientError"
    error.__class__.__module__ = "google.genai"

    result = extract_error_message(error)
    assert result == "Google: API key not valid"


def test_should_log_error_known_errors():
    """Test that known errors should not be logged."""
    from asyncio import CancelledError

    # Known errors that shouldn't be logged
    assert not should_log_error(CancelledError())
    assert not should_log_error(KeyboardInterrupt())
    assert not should_log_error(
        ModelHTTPError(
            status_code=400,
            model_name="test",
            body={},
        )
    )


def test_should_log_error_unknown_errors():
    """Test that unknown errors should be logged."""
    assert should_log_error(ValueError("test"))
    assert should_log_error(Exception("test"))
    assert should_log_error(RuntimeError("test"))


def test_save_error_log():
    """Test saving error log to file."""
    error = ValueError("Test error message")

    log_file = save_error_log(error)

    # Check file exists
    assert log_file.exists()
    assert log_file.name.startswith("sidekick_error_")
    assert log_file.suffix == ".log"

    # Check content
    content = log_file.read_text()
    assert "Sidekick Error Log" in content
    assert "Test error message" in content
    assert "ValueError" in content
    assert "Traceback" in content

    # Clean up
    log_file.unlink()


@pytest.mark.asyncio
async def test_handle_error_with_logging():
    """Test handle_error function with error that should be logged."""
    mock_display = MagicMock()
    error = ValueError("Unexpected error")

    await handle_error(error, mock_display)

    # Check display function was called
    mock_display.assert_called_once()
    call_args = mock_display.call_args

    # Check message
    assert "ValueError" in call_args[0][0]
    assert "Unexpected error" in call_args[0][0]

    # Check detail contains log file path
    assert "detail" in call_args[1]
    assert "Error log:" in call_args[1]["detail"]
    assert "sidekick_error_" in call_args[1]["detail"]


@pytest.mark.asyncio
async def test_handle_error_without_logging():
    """Test handle_error function with error that shouldn't be logged."""
    mock_display = MagicMock()
    error = ModelHTTPError(
        status_code=400,
        model_name="TestModel",
        body={"error": {"message": "Bad request"}},
    )

    await handle_error(error, mock_display)

    # Check display function was called without detail
    mock_display.assert_called_once_with("TestModel: Bad request")


def test_extract_error_message_with_regex_extraction():
    """Test that regex extraction works for embedded messages."""
    # Test with a complex error message containing embedded JSON-like structure
    error_msg = (
        'APIError: {"error": {"message": "Your credit balance is too low", '
        '"type": "insufficient_funds", "code": 1234}}'
    )
    error = Exception(error_msg)

    result = extract_error_message(error)
    assert "Your credit balance is too low" in result
