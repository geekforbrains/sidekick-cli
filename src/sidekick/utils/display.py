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
