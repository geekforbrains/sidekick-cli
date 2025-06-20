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


def test_handles_server_creation_failure(caplog):
    """Test handles individual server creation failures gracefully."""
    mock_config = {
        "default_model": "test",
        "env": {},
        "mcpServers": {
            "valid": {"command": "uvx", "args": ["mcp-server-fetch"]},
            "failing": {"command": "test", "args": ["test"]},
        },
    }

    with patch("sidekick.mcp.servers.read_config_file", return_value=mock_config):
        # Make create_mcp_server fail for one server
        original_create = __import__(
            "sidekick.mcp.servers", fromlist=["create_mcp_server"]
        ).create_mcp_server

        def mock_create(key, config):
            if key == "failing":
                raise RuntimeError("Simulated server creation failure")
            return original_create(key, config)

        with patch("sidekick.mcp.servers.create_mcp_server", side_effect=mock_create):
            with caplog.at_level(logging.WARNING):
                servers = load_mcp_servers()

    assert len(servers) == 1
    assert servers[0].display_name == "Valid"
    assert "Failed to create server 'failing'" in caplog.text


def test_warns_when_all_servers_fail(caplog):
    """Test warns when no servers could be created."""
    mock_config = {
        "default_model": "test",
        "env": {},
        "mcpServers": {
            "server1": {"command": "test1", "args": ["test"]},
            "server2": {"command": "test2", "args": ["test"]},
        },
    }

    with patch("sidekick.mcp.servers.read_config_file", return_value=mock_config):
        # Make all server creations fail
        with patch("sidekick.mcp.servers.create_mcp_server", side_effect=Exception("Failed")):
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
