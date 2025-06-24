"""Simplified error handling for Sidekick CLI."""

import asyncio
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

from pydantic_ai.exceptions import ModelHTTPError


async def handle_error(error: Exception, display_func) -> None:
    """Handle any error in the application.

    Args:
        error: The exception to handle
        display_func: Function to display error (typically ui.error)
    """
    # Extract user-friendly message
    message = extract_error_message(error)

    # Log if it's unexpected
    if should_log_error(error):
        log_file = save_error_log(error)
        display_func(message, detail=f"Error log: {log_file}")
    else:
        display_func(message)


def extract_error_message(error: Exception) -> str:
    """Extract a clean error message from any exception."""
    # Handle known patterns
    if isinstance(error, ModelHTTPError):
        return f"{error.model_name}: {_get_api_message(error)}"

    error_str = str(error)

    # Handle specific error patterns
    if "MALFORMED_FUNCTION_CALL" in error_str:
        return "The AI model had trouble executing a function. Please try again."

    if "Content field missing" in error_str:
        return (
            "The AI model returned an unexpected response format. This might be a temporary issue."
        )

    # Try to extract clean error messages from provider-specific errors
    error_type = type(error).__name__
    module_name = type(error).__module__ if hasattr(type(error), "__module__") else ""

    # Check for provider-specific client errors
    if error_type in ["ClientError", "APIStatusError", "BadRequestError", "AuthenticationError"]:
        clean_msg = _extract_provider_message(error)
        if clean_msg:
            provider = _get_provider_name(module_name)
            return f"{provider}: {clean_msg}"

    # For unknown errors, clean up the message
    if len(error_str) > 150:
        # Try to extract just a message part if it's very long
        import re

        message_match = re.search(
            r'["\']?message["\']?:\s*["\']([^"\'\n]+)["\']', error_str, re.IGNORECASE
        )
        if message_match:
            error_str = message_match.group(1)
        else:
            error_str = error_str[:150] + "..."

    return f"Unexpected error ({error_type}): {error_str}"


def should_log_error(error: Exception) -> bool:
    """Determine if error should be logged to file."""
    # Known/expected errors don't need logging
    known_errors = (asyncio.CancelledError, KeyboardInterrupt, ModelHTTPError)
    return not isinstance(error, known_errors)


def save_error_log(error: Exception) -> Path:
    """Save error traceback to a temp file and return the path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = Path(tempfile.gettempdir())
    log_file = temp_dir / f"sidekick_error_{timestamp}.log"

    tb = traceback.format_exc()

    with open(log_file, "w") as f:
        f.write("Sidekick Error Log\n")
        f.write("==================\n\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Error Type: {type(error).__name__}\n")
        module = type(error).__module__ if hasattr(type(error), "__module__") else "Unknown"
        f.write(f"Error Module: {module}\n\n")
        f.write(f"Error Message:\n{str(error)}\n\n")
        f.write(f"Full Traceback:\n{tb}")

    return log_file


def _get_api_message(error: ModelHTTPError) -> str:
    """Extract API error message from ModelHTTPError."""
    error_msg = str(error)
    if isinstance(error.body, dict):
        # Try to extract message from common error structures
        if "error" in error.body and isinstance(error.body["error"], dict):
            error_msg = error.body["error"].get("message", str(error))
        elif "message" in error.body:
            error_msg = error.body["message"]
    return error_msg


def _extract_provider_message(error: Exception) -> str:
    """Extract clean message from provider-specific errors."""
    # Try various attributes that providers use
    if hasattr(error, "message"):
        return error.message
    elif hasattr(error, "body") and isinstance(error.body, dict):
        # OpenAI/Anthropic pattern
        if "error" in error.body and isinstance(error.body["error"], dict):
            return error.body["error"].get("message", "")
        elif "message" in error.body:
            return error.body["message"]
    elif hasattr(error, "details") and isinstance(error.details, dict):
        # Google pattern
        if "error" in error.details and isinstance(error.details["error"], dict):
            return error.details["error"].get("message", "")
        elif "message" in error.details:
            return error.details["message"]
    return ""


def _get_provider_name(module_name: str) -> str:
    """Get provider name from module name."""
    if "openai" in module_name:
        return "OpenAI"
    elif "anthropic" in module_name:
        return "Anthropic"
    elif "google" in module_name or "genai" in module_name:
        return "Google"
    return "Provider"
