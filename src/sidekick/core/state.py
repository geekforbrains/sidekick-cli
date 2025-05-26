"""Module: sidekick.core.state

State management system for session data in Sidekick CLI.
Provides centralized state tracking for agents, messages, configurations, and session information.
"""

from sidekick.types import SessionState


class StateManager:
    def __init__(self):
        self._session = SessionState()

    @property
    def session(self) -> SessionState:
        return self._session

    def reset_session(self):
        self._session = SessionState()
