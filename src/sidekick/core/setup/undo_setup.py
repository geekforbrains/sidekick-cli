"""Module: sidekick.core.setup.undo_setup

Undo system initialization for the Sidekick CLI.
Sets up file tracking and state management for undo operations.
"""

from sidekick.core.setup.base import BaseSetup
from sidekick.core.state import StateManager
from sidekick.services.undo_service import init_undo_system


class UndoSetup(BaseSetup):
    """Setup step for undo system initialization."""

    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)

    @property
    def name(self) -> str:
        return "Undo System"

    async def should_run(self, force_setup: bool = False) -> bool:
        """Undo setup should run if not already initialized."""
        return not self.state_manager.session.undo_initialized

    async def execute(self, force_setup: bool = False) -> None:
        """Initialize the undo system."""
        self.state_manager.session.undo_initialized = init_undo_system(self.state_manager)

    async def validate(self) -> bool:
        """Validate that undo system was initialized correctly."""
        return self.state_manager.session.undo_initialized
