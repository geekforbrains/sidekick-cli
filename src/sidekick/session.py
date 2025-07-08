from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set


@dataclass
class Session:
    current_model: Optional[str] = None
    allowed_commands: Set[str] = field(default_factory=set)
    disabled_confirmations: Set[str] = field(default_factory=set)
    confirmation_enabled: bool = True
    debug_enabled: bool = False

    def init(self, config: Dict[str, Any], model: str):
        """Initialize the session state."""
        self.current_model = model

        if "settings" in config:
            if "allowed_commands" in config["settings"]:
                self.allowed_commands.update(config["settings"]["allowed_commands"])


# Create global session instance
session = Session()
