import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set


@dataclass
class Session:
    current_model: Optional[str] = None
    agents: Dict = field(default_factory=dict)
    messages: list = field(default_factory=list)
    spinner: Any = None
    current_task: Optional[asyncio.Task] = None
    sigint_received: bool = False
    skip_confirmations: Set[str] = field(default_factory=set)
    allowed_commands: Set[str] = field(default_factory=set)
    confirmation_enabled: bool = True
    model_switched: bool = False

    # Usage tracking
    tool_usage: Dict[str, int] = field(default_factory=dict)
    last_usage: Optional[Dict[str, Any]] = None
    total_tokens: int = 0
    total_cost: float = 0.0

    def init(self, config: Dict[str, Any], model: str):
        """Initialize the session state."""
        self.current_model = model

        if "settings" in config:
            # Support new allowed_tools field
            if "allowed_tools" in config["settings"]:
                self.skip_confirmations.update(config["settings"]["allowed_tools"])

            # Backward compatibility with tool_ignore
            if "tool_ignore" in config["settings"]:
                self.skip_confirmations.update(config["settings"]["tool_ignore"])

            if "allowed_commands" in config["settings"]:
                self.allowed_commands.update(config["settings"]["allowed_commands"])


# Create global session instance
session = Session()
