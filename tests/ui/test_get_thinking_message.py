"""Test get_thinking_message function."""

from sidekick.ui import THINKING_MESSAGES, get_thinking_message


def test_returns_message_from_list():
    """Test that get_thinking_message returns a message from the list."""
    message = get_thinking_message()
    assert message in THINKING_MESSAGES


def test_returns_string():
    """Test that get_thinking_message returns a non-empty string."""
    message = get_thinking_message()
    assert isinstance(message, str)
    assert len(message) > 0


def test_multiple_calls_work():
    """Test that multiple calls work consistently."""
    for _ in range(10):
        message = get_thinking_message()
        assert message in THINKING_MESSAGES
