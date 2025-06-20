"""Tests for set_env_vars function."""

import os
from unittest.mock import patch

from sidekick.config import set_env_vars


def test_sets_string_env_vars():
    """Test that string environment variables are set."""
    env_dict = {"API_KEY": "test-key", "ANOTHER_VAR": "test-value"}

    with patch.dict(os.environ, {}, clear=True):
        set_env_vars(env_dict)
        assert os.environ.get("API_KEY") == "test-key"
        assert os.environ.get("ANOTHER_VAR") == "test-value"


def test_skips_empty_values():
    """Test that empty string values are skipped."""
    env_dict = {"API_KEY": "test-key", "EMPTY_VAR": ""}

    with patch.dict(os.environ, {}, clear=True):
        set_env_vars(env_dict)
        assert os.environ.get("API_KEY") == "test-key"
        assert "EMPTY_VAR" not in os.environ


def test_skips_non_string_values():
    """Test that non-string values are skipped."""
    env_dict = {"API_KEY": "test-key", "NUMBER_VAR": 123, "BOOL_VAR": True, "NONE_VAR": None}

    with patch.dict(os.environ, {}, clear=True):
        set_env_vars(env_dict)
        assert os.environ.get("API_KEY") == "test-key"
        assert "NUMBER_VAR" not in os.environ
        assert "BOOL_VAR" not in os.environ
        assert "NONE_VAR" not in os.environ


def test_handles_empty_dict():
    """Test that empty dict is handled gracefully."""
    with patch.dict(os.environ, {"EXISTING": "value"}, clear=True):
        set_env_vars({})
        # Should not change existing env
        assert os.environ.get("EXISTING") == "value"
