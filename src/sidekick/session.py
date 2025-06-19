from typing import Any, Dict, Optional

user_config: Optional[Dict[str, Any]] = None
current_model: Optional[str] = None
agents: Dict = {}
messages: list = []
spinner: Any = None


def init(config: Dict[str, Any], model: str):
    """Initialize the session state."""
    global user_config, current_model
    user_config = config
    current_model = model
