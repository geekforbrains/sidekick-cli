"""Tests for validate_server_config function."""

import pytest

from sidekick.mcp.servers import validate_server_config


def test_valid_config_passes():
    """Test that valid server config passes validation."""
    config = {
        "command": "uvx",
        "args": ["mcp-server-fetch"]
    }
    # Should not raise
    validate_server_config("test-server", config)


def test_valid_config_with_multiple_args():
    """Test valid config with multiple args."""
    config = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"]
    }
    # Should not raise
    validate_server_config("test-server", config)


def test_raises_for_non_dict():
    """Test ValueError for non-dict config."""
    with pytest.raises(ValueError) as exc_info:
        validate_server_config("test-server", "not a dict")
    assert "Server 'test-server' configuration must be a dictionary" in str(exc_info.value)


def test_raises_for_missing_command():
    """Test ValueError when command missing."""
    with pytest.raises(ValueError) as exc_info:
        validate_server_config("test-server", {"args": ["test"]})
    assert "Server 'test-server' missing required field 'command'" in str(exc_info.value)


def test_raises_for_empty_command():
    """Test ValueError when command is empty."""
    with pytest.raises(ValueError) as exc_info:
        validate_server_config("test-server", {"command": "", "args": ["test"]})
    assert "Server 'test-server' has empty command" in str(exc_info.value)


def test_raises_for_missing_args():
    """Test ValueError when args missing."""
    with pytest.raises(ValueError) as exc_info:
        validate_server_config("test-server", {"command": "uvx"})
    assert "Server 'test-server' missing required field 'args'" in str(exc_info.value)


def test_raises_for_non_list_args():
    """Test ValueError when args is not a list."""
    with pytest.raises(ValueError) as exc_info:
        validate_server_config("test-server", {"command": "uvx", "args": "not-a-list"})
    assert "Server 'test-server' field 'args' must be a list" in str(exc_info.value)


def test_raises_for_empty_args():
    """Test ValueError when args is empty list."""
    with pytest.raises(ValueError) as exc_info:
        validate_server_config("test-server", {"command": "uvx", "args": []})
    assert "Server 'test-server' field 'args' must contain at least one argument" in str(exc_info.value)


def test_accepts_optional_fields():
    """Test that optional fields are accepted."""
    config = {
        "command": "uvx",
        "args": ["mcp-server-fetch"],
        "env": {"API_KEY": "test"},
        "name": "Custom Name"
    }
    # Should not raise
    validate_server_config("test-server", config)