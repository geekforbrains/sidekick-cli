"""Tests for _format_display_name function."""

from sidekick.mcp.servers import _format_display_name


def test_converts_simple_lowercase():
    """Test conversion of simple lowercase name."""
    assert _format_display_name("fetch") == "Fetch"


def test_converts_hyphenated_names():
    """Test conversion of hyphenated names."""
    assert _format_display_name("brave-search") == "Brave Search"
    assert _format_display_name("mcp-server-fetch") == "Mcp Server Fetch"


def test_converts_underscored_names():
    """Test conversion of underscored names."""
    assert _format_display_name("brave_search") == "Brave Search"
    assert _format_display_name("mcp_server_fetch") == "Mcp Server Fetch"


def test_converts_mixed_separators():
    """Test conversion with mixed separators."""
    assert _format_display_name("brave-search_api") == "Brave Search Api"
    assert _format_display_name("mcp_server-fetch") == "Mcp Server Fetch"


def test_handles_already_capitalized():
    """Test handling of already capitalized input."""
    assert _format_display_name("FETCH") == "Fetch"
    assert _format_display_name("Brave-Search") == "Brave Search"


def test_handles_empty_string():
    """Test handling of empty string."""
    assert _format_display_name("") == ""
