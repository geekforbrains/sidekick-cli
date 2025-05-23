from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid


@dataclass
class SessionState:
    user_config: Dict[str, Any] = field(default_factory=dict)
    agents: Dict[str, Any] = field(default_factory=dict)
    messages: List[Any] = field(default_factory=list)
    total_cost: float = 0.0
    current_model: str = "openai:gpt-4o"
    spinner: Optional[Any] = None
    tool_ignore: List[str] = field(default_factory=list)
    yolo: bool = False
    undo_initialized: bool = False
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: Optional[str] = None
    telemetry_enabled: bool = True
    input_sessions: Dict[str, Any] = field(default_factory=dict)
    current_task: Optional[Any] = None


class StateManager:
    def __init__(self):
        self._session = SessionState()
    
    @property
    def session(self) -> SessionState:
        return self._session
    
    def reset_session(self):
        self._session = SessionState()