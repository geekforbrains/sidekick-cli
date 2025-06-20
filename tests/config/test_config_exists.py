"""Tests for config_exists function."""

from unittest.mock import patch

from sidekick.config import config_exists


def test_returns_true_when_exists():
    """Test config_exists returns True when file exists."""
    with patch("pathlib.Path.exists", return_value=True):
        assert config_exists() is True


def test_returns_false_when_not_exists():
    """Test config_exists returns False when file doesn't exist."""
    with patch("pathlib.Path.exists", return_value=False):
        assert config_exists() is False
