from typing import Any, Dict, Optional
import asyncio

user_config: Optional[Dict[str, Any]] = None
current_model: Optional[str] = None
agents: Dict = {}
messages: list = []
spinner: Any = None
current_task: Optional[asyncio.Task] = None
sigint_received: bool = False


def init(config: Dict[str, Any], model: str):
    """Initialize the session state."""
    global user_config, current_model
    user_config = config
    current_model = model
