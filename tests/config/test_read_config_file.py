"""Tests for read_config_file function."""

from unittest.mock import mock_open, patch

import pytest

from sidekick.config import ConfigError, ConfigValidationError, read_config_file


def test_reads_valid_json():
    """Test reading valid JSON config."""
    mock_json = '{"default_model": "test-model", "env": {}}'
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_json)):
            config = read_config_file()
            assert config == {"default_model": "test-model", "env": {}}


def test_raises_file_not_found():
    """Test ConfigError when config doesn't exist."""
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(ConfigError) as exc_info:
            read_config_file()
        assert "Config file not found" in str(exc_info.value)


def test_raises_permission_error():
    """Test ConfigError when can't access file."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(ConfigError) as exc_info:
                read_config_file()
            assert "Cannot access config file" in str(exc_info.value)


def test_raises_json_decode_error():
    """Test ConfigValidationError for invalid JSON."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with pytest.raises(ConfigValidationError):
                read_config_file()
