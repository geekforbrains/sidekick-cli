from typing import Any, Dict


class SessionState:
    def __init__(self, user_config: Dict[str, Any], current_model: str):
        self.user_config = user_config
        self.current_model = current_model
        self.agents = {}
        self.messages = []
