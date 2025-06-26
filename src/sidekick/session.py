import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set


@dataclass
class Session:
    current_model: Optional[str] = None
    agents: Dict = field(default_factory=dict)
    messages: list = field(default_factory=list)
    spinner: Any = None
    spinner_rotation_task: Optional[asyncio.Task] = None
    current_task: Optional[asyncio.Task] = None
    sigint_received: bool = False
    allowed_commands: Set[str] = field(default_factory=set)
    disabled_confirmations: Set[str] = field(default_factory=set)
    confirmation_enabled: bool = True
    model_switched: bool = False
    last_usage: Optional[Dict[str, Any]] = None
    total_tokens: int = 0
    total_cost: float = 0.0
    debug_enabled: bool = False
    log_file: Optional[str] = None

    def init(self, config: Dict[str, Any], model: str):
        """Initialize the session state."""
        self.current_model = model

        if "settings" in config:
            if "allowed_commands" in config["settings"]:
                self.allowed_commands.update(config["settings"]["allowed_commands"])


# Create global session instance
session = Session()
