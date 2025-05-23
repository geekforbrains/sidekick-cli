"""Module: sidekick.core.state

State management system for session data in Sidekick CLI.
Provides centralized state tracking for agents, messages, configurations, and session information.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from sidekick.types import (DeviceId, InputSessions, MessageHistory, ModelName, SessionId, ToolName,
                            UserConfig)


@dataclass
class SessionState:
    user_config: UserConfig = field(default_factory=dict)
    agents: dict[str, Any] = field(
        default_factory=dict
    )  # Keep as dict[str, Any] for agent instances
    messages: MessageHistory = field(default_factory=list)
    total_cost: float = 0.0
    current_model: ModelName = "openai:gpt-4o"
    spinner: Optional[Any] = None
    tool_ignore: list[ToolName] = field(default_factory=list)
    yolo: bool = False
    undo_initialized: bool = False
    session_id: SessionId = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: Optional[DeviceId] = None
    telemetry_enabled: bool = True
    input_sessions: InputSessions = field(default_factory=dict)
    current_task: Optional[Any] = None


class StateManager:
    def __init__(self):
        self._session = SessionState()

    @property
    def session(self) -> SessionState:
        return self._session

    def reset_session(self):
        self._session = SessionState()
