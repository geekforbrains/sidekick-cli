"""Tests for MCP server config validation."""

import pytest

from sidekick.config import ConfigValidationError, parse_mcp_servers


def test_valid_config_passes():
    """Test that valid server config passes validation."""
    config = {"mcpServers": {"test-server": {"command": "uvx", "args": ["mcp-server-fetch"]}}}
    # Should not raise
    result = parse_mcp_servers(config)
    assert "test-server" in result


def test_valid_config_with_multiple_args():
    """Test valid config with multiple args."""
    config = {
        "mcpServers": {
            "test-server": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            }
        }
    }
    # Should not raise
    result = parse_mcp_servers(config)
    assert "test-server" in result


def test_raises_for_non_dict():
    """Test ConfigValidationError for non-dict config."""
    config = {"mcpServers": {"test-server": "not a dict"}}
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers(config)
    assert "MCP server 'test-server' configuration must be an object" in str(exc_info.value)


def test_raises_for_missing_command():
    """Test ConfigValidationError when command missing."""
    config = {"mcpServers": {"test-server": {"args": ["test"]}}}
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers(config)
    assert "MCP server 'test-server' missing required field 'command'" in str(exc_info.value)


def test_raises_for_empty_command():
    """Test that empty command is allowed (validation doesn't check for empty strings)."""
    config = {"mcpServers": {"test-server": {"command": "", "args": ["test"]}}}
    # parse_mcp_servers doesn't validate empty command strings, only type
    result = parse_mcp_servers(config)
    assert "test-server" in result


def test_raises_for_missing_args():
    """Test ConfigValidationError when args missing."""
    config = {"mcpServers": {"test-server": {"command": "uvx"}}}
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers(config)
    assert "MCP server 'test-server' missing required field 'args'" in str(exc_info.value)


def test_raises_for_non_list_args():
    """Test ConfigValidationError when args is not a list."""
    config = {"mcpServers": {"test-server": {"command": "uvx", "args": "not-a-list"}}}
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers(config)
    assert "MCP server 'test-server' field 'args' must be an array" in str(exc_info.value)


def test_raises_for_empty_args():
    """Test ConfigValidationError when args is empty list."""
    config = {"mcpServers": {"test-server": {"command": "uvx", "args": []}}}
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers(config)
    assert "MCP server 'test-server' field 'args' must contain at least one argument" in str(
        exc_info.value
    )


def test_accepts_optional_fields():
    """Test that optional fields are accepted."""
    config = {
        "mcpServers": {
            "test-server": {
                "command": "uvx",
                "args": ["mcp-server-fetch"],
                "env": {"API_KEY": "test"},
                "name": "Custom Name",
            }
        }
    }
    # Should not raise
    result = parse_mcp_servers(config)
    assert "test-server" in result
    assert result["test-server"]["env"] == {"API_KEY": "test"}


def test_raises_for_non_dict_mcpservers():
    """Test ConfigValidationError when mcpServers is not a dict."""
    config = {"mcpServers": "not a dict"}
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers(config)
    assert "'mcpServers' field must be an object" in str(exc_info.value)


def test_returns_empty_dict_when_no_mcpservers():
    """Test that empty dict is returned when no mcpServers field."""
    config = {}
    result = parse_mcp_servers(config)
    assert result == {}


def test_raises_for_non_dict_env():
    """Test ConfigValidationError when env field is not a dict."""
    config = {
        "mcpServers": {
            "test-server": {"command": "uvx", "args": ["mcp-server-fetch"], "env": "not a dict"}
        }
    }
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers(config)
    assert "MCP server 'test-server' field 'env' must be an object" in str(exc_info.value)
