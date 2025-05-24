"""Module: sidekick.core.setup.undo_setup

Undo system initialization for the Sidekick CLI.
Sets up file tracking and state management for undo operations.
"""

from pathlib import Path

from sidekick.constants import UNDO_DISABLED_HOME, UNDO_DISABLED_NO_GIT
from sidekick.core.setup.base import BaseSetup
from sidekick.core.state import StateManager
from sidekick.services.undo_service import init_undo_system, is_in_git_project
from sidekick.ui import console as ui


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
        cwd = Path.cwd()
        home_dir = Path.home()
        
        if cwd == home_dir:
            await ui.muted(UNDO_DISABLED_HOME)
            self.state_manager.session.undo_initialized = True  # Setup completed, but disabled
            return
            
        if not is_in_git_project():
            await ui.muted(UNDO_DISABLED_NO_GIT)
            self.state_manager.session.undo_initialized = True  # Setup completed, but disabled
            return
            
        # Try to actually initialize undo system
        success = init_undo_system(self.state_manager)
        if not success:
            await ui.warning("Failed to initialize undo system")
        self.state_manager.session.undo_initialized = success

    async def validate(self) -> bool:
        """Validate that undo system was initialized correctly."""
        return self.state_manager.session.undo_initialized
