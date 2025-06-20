"""Tests for parse_mcp_servers function."""

import pytest

from sidekick.config import parse_mcp_servers, ConfigValidationError


def test_returns_empty_dict_when_no_mcp_servers():
    """Test returns empty dict when mcpServers not present."""
    config = {"default_model": "test", "env": {}}
    assert parse_mcp_servers(config) == {}


def test_returns_valid_mcp_servers():
    """Test returns MCP servers when valid."""
    config = {
        "mcpServers": {
            "fetch": {
                "command": "uvx",
                "args": ["mcp-server-fetch"]
            }
        }
    }
    result = parse_mcp_servers(config)
    assert result == config["mcpServers"]


def test_accepts_server_with_name_field():
    """Test accepts server config with optional name field."""
    config = {
        "mcpServers": {
            "fetch": {
                "command": "uvx",
                "args": ["mcp-server-fetch"],
                "name": "Fetch Server"
            }
        }
    }
    result = parse_mcp_servers(config)
    assert result == config["mcpServers"]


def test_accepts_server_with_env():
    """Test accepts server config with env vars."""
    config = {
        "mcpServers": {
            "brave": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {"BRAVE_API_KEY": "test-key"}
            }
        }
    }
    result = parse_mcp_servers(config)
    assert result == config["mcpServers"]


def test_raises_for_non_dict_mcp_servers():
    """Test ConfigValidationError when mcpServers not dict."""
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers({"mcpServers": "not a dict"})
    assert "'mcpServers' field must be an object" in str(exc_info.value)


def test_raises_for_invalid_server_config():
    """Test ConfigValidationError for invalid server config."""
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers({
            "mcpServers": {
                "fetch": "not a dict"
            }
        })
    assert "MCP server 'fetch' configuration must be an object" in str(exc_info.value)


def test_raises_for_missing_command():
    """Test ConfigValidationError when command missing."""
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers({
            "mcpServers": {
                "fetch": {"args": []}
            }
        })
    assert "MCP server 'fetch' missing required field 'command'" in str(exc_info.value)


def test_raises_for_missing_args():
    """Test ConfigValidationError when args missing."""
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers({
            "mcpServers": {
                "fetch": {"command": "uvx"}
            }
        })
    assert "MCP server 'fetch' missing required field 'args'" in str(exc_info.value)


def test_raises_for_non_string_command():
    """Test ConfigValidationError when command not string."""
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers({
            "mcpServers": {
                "fetch": {"command": 123}
            }
        })
    assert "MCP server 'fetch' field 'command' must be a string" in str(exc_info.value)


def test_raises_for_non_list_args():
    """Test ConfigValidationError when args not list."""
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers({
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": "not a list"
                }
            }
        })
    assert "MCP server 'fetch' field 'args' must be an array" in str(exc_info.value)


def test_raises_for_empty_args():
    """Test ConfigValidationError when args is empty list."""
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers({
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": []
                }
            }
        })
    assert "MCP server 'fetch' field 'args' must contain at least one argument" in str(exc_info.value)


def test_raises_for_non_dict_env():
    """Test ConfigValidationError when env not dict."""
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_mcp_servers({
            "mcpServers": {
                "fetch": {
                    "command": "uvx",
                    "args": ["mcp-server-fetch"],
                    "env": "not a dict"
                }
            }
        })
    assert "MCP server 'fetch' field 'env' must be an object" in str(exc_info.value)