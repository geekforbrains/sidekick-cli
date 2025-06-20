"""Tests for format_server_name function."""

from sidekick.utils.display import format_server_name


def test_converts_simple_lowercase():
    """Test conversion of simple lowercase name."""
    assert format_server_name("fetch") == "Fetch"


def test_converts_hyphenated_names():
    """Test conversion of hyphenated names."""
    assert format_server_name("brave-search") == "Brave Search"
    assert format_server_name("mcp-server-fetch") == "Mcp Server Fetch"


def test_converts_underscored_names():
    """Test conversion of underscored names."""
    assert format_server_name("brave_search") == "Brave Search"
    assert format_server_name("mcp_server_fetch") == "Mcp Server Fetch"


def test_converts_mixed_separators():
    """Test conversion with mixed separators."""
    assert format_server_name("brave-search_api") == "Brave Search Api"
    assert format_server_name("mcp_server-fetch") == "Mcp Server Fetch"


def test_handles_already_capitalized():
    """Test handling of already capitalized input."""
    assert format_server_name("FETCH") == "Fetch"
    assert format_server_name("Brave-Search") == "Brave Search"


def test_handles_empty_string():
    """Test handling of empty string."""
    assert format_server_name("") == ""
