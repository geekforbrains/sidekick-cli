"""Tests for create_mcp_server function."""

from sidekick.mcp.servers import SilentMCPServerStdio, create_mcp_server


def test_creates_server_with_minimal_config():
    """Test creating server with minimal valid config."""
    config = {"command": "uvx", "args": ["mcp-server-fetch"]}

    server = create_mcp_server("fetch", config)

    assert isinstance(server, SilentMCPServerStdio)
    assert server.command == "uvx"
    assert server.args == ["mcp-server-fetch"]
    assert server.env == {}
    assert server.display_name == "Fetch"


def test_creates_server_with_custom_name():
    """Test creating server with custom name field."""
    config = {"command": "uvx", "args": ["mcp-server-fetch"], "name": "Custom Fetch Server"}

    server = create_mcp_server("fetch", config)

    assert server.display_name == "Custom Fetch Server"


def test_creates_server_with_env_vars():
    """Test creating server with environment variables."""
    config = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {"BRAVE_API_KEY": "test-key"},
    }

    server = create_mcp_server("brave-search", config)

    assert server.env == {"BRAVE_API_KEY": "test-key"}
    assert server.display_name == "Brave Search"


def test_formats_display_name_from_key():
    """Test display name formatting from server key."""
    config = {"command": "test", "args": ["arg"]}

    # Test various key formats
    server1 = create_mcp_server("simple", config)
    assert server1.display_name == "Simple"

    server2 = create_mcp_server("hyphen-name", config)
    assert server2.display_name == "Hyphen Name"

    server3 = create_mcp_server("underscore_name", config)
    assert server3.display_name == "Underscore Name"
