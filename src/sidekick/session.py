import asyncio
from typing import Any, Dict, Optional, Set

current_model: Optional[str] = None
agents: Dict = {}
messages: list = []
spinner: Any = None
current_task: Optional[asyncio.Task] = None
sigint_received: bool = False
skip_confirmations: Set[str] = set()  # Tools that user selected "always" for
confirmation_enabled: bool = True  # Global flag to enable/disable confirmations


def init(config: Dict[str, Any], model: str):
    """Initialize the session state."""
    global current_model
    current_model = model

    # Load default allowed tools from config
    if "settings" in config and "tool_ignore" in config["settings"]:
        skip_confirmations.update(config["settings"]["tool_ignore"])
