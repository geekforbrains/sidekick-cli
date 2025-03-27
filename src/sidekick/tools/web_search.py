import os
import urllib.parse

import requests

from sidekick.utils import ui


def web_search(query: str) -> str:
    """
    Make a web search for the given query.

    Args:
        ctx: Run context from the agent
        query: The search query

    Returns:
        Search results as a JSON string
    """
    ui.status(f"Search({query})")

    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not api_key:
        msg = "BRAVE_SEARCH_API_KEY is not configured"
        msg += " in ~/.config/sidekick.json"
        raise Exception(msg)

    encoded_query = urllib.parse.quote(query)
    url = f"https://api.search.brave.com/res/v1/web/search?q={encoded_query}"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        ui.error(f"Error searching: {e}")
        return f"Failed to search for '{query}' with error: {e}"
