from typing import Any, Dict, Optional
import asyncio

current_model: Optional[str] = None
agents: Dict = {}
messages: list = []
spinner: Any = None
current_task: Optional[asyncio.Task] = None
sigint_received: bool = False


def init(config: Dict[str, Any], model: str):
    """Initialize the session state."""
    global current_model
    current_model = model