"""Tests for get_config_path function."""

from pathlib import Path

from sidekick.config import get_config_path


def test_returns_correct_path():
    """Test that get_config_path returns the expected path."""
    expected = Path.home() / ".config" / "sidekick.json"
    assert get_config_path() == expected
