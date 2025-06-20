"""Tests for load_mcp_servers function."""

import logging
from unittest.mock import patch

from sidekick.config import ConfigError
from sidekick.mcp.servers import load_mcp_servers


def test_loads_valid_servers():
    """Test loading valid MCP servers from config."""
    mock_config = {
        "default_model": "test",
        "env": {},
        "mcpServers": {
            "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
            "brave": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {"BRAVE_API_KEY": "test"},
            },
        },
    }

    with patch("sidekick.mcp.servers.read_config_file", return_value=mock_config):
        servers = load_mcp_servers()

    assert len(servers) == 2
    assert servers[0].display_name == "Fetch"
    assert servers[1].display_name == "Brave"


def test_returns_empty_list_when_no_mcp_servers():
    """Test returns empty list when no mcpServers in config."""
    mock_config = {"default_model": "test", "env": {}}

    with patch("sidekick.mcp.servers.read_config_file", return_value=mock_config):
        servers = load_mcp_servers()

    assert servers == []


def test_returns_empty_list_on_config_error():
    """Test returns empty list when config loading fails."""
    with patch("sidekick.mcp.servers.read_config_file", side_effect=ConfigError("Test error")):
        servers = load_mcp_servers()

    assert servers == []


def test_skips_invalid_servers(caplog):
    """Test skips invalid servers and continues with valid ones."""
    mock_config = {
        "default_model": "test",
        "env": {},
        "mcpServers": {
            "valid": {"command": "uvx", "args": ["mcp-server-fetch"]},
            "invalid": {"command": "", "args": ["test"]},
            "also-valid": {"command": "npx", "args": ["test"]},
        },
    }

    with patch("sidekick.mcp.servers.read_config_file", return_value=mock_config):
        with patch("sidekick.mcp.servers.validate_config_structure"):
            with patch(
                "sidekick.mcp.servers.parse_mcp_servers", return_value=mock_config["mcpServers"]
            ):
                with caplog.at_level(logging.WARNING):
                    servers = load_mcp_servers()

    assert len(servers) == 2
    assert servers[0].display_name == "Valid"
    assert servers[1].display_name == "Also Valid"
    assert "Skipping invalid server 'invalid'" in caplog.text


def test_warns_when_all_servers_invalid(caplog):
    """Test warns when no valid servers could be loaded."""
    mock_config = {
        "default_model": "test",
        "env": {},
        "mcpServers": {
            "invalid1": {"command": "", "args": ["test"]},
            "invalid2": {"command": "test", "args": []},
        },
    }

    with patch("sidekick.mcp.servers.read_config_file", return_value=mock_config):
        with patch("sidekick.mcp.servers.validate_config_structure"):
            with patch(
                "sidekick.mcp.servers.parse_mcp_servers", return_value=mock_config["mcpServers"]
            ):
                with caplog.at_level(logging.WARNING):
                    servers = load_mcp_servers()

    assert servers == []
    assert "No valid MCP servers could be loaded" in caplog.text


def test_handles_unexpected_errors(caplog):
    """Test handles unexpected errors gracefully."""
    with patch("sidekick.mcp.servers.read_config_file", side_effect=Exception("Unexpected")):
        with caplog.at_level(logging.ERROR):
            servers = load_mcp_servers()

    assert servers == []
    assert "Unexpected error loading config" in caplog.text
