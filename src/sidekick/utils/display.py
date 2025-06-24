from typing import Dict

TOOL_DISPLAY_NAMES: Dict[str, str] = {
    "read_file": "ReadFile",
    "write_file": "WriteFile",
    "update_file": "UpdateFile",
    "run_command": "Run",
    "git_add": "GitAdd",
    "git_commit": "GitCommit",
    "search_files": "SearchFiles",
    "search_dirs": "SearchDirs",
    "search_content": "SearchContent",
    "list_directory": "List",
}


def format_tool_name(tool_name: str) -> str:
    """Format tool name for display.

    Args:
        tool_name: The internal tool name

    Returns:
        Human-readable display name
    """
    if tool_name in TOOL_DISPLAY_NAMES:
        return TOOL_DISPLAY_NAMES[tool_name]
    else:
        return f"MCP({tool_name})"


def format_server_name(key: str) -> str:
    """Convert a server key to a display name.

    Examples:
        fetch -> Fetch
        brave-search -> Brave Search
        brave_search -> Brave Search

    Args:
        key: The server key/identifier

    Returns:
        Human-readable display name
    """
    return key.replace("-", " ").replace("_", " ").title()
