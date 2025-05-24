"""Module: sidekick.core.setup.undo_setup

Undo system initialization for the Sidekick CLI.
Sets up file tracking and state management for undo operations.
"""

from pathlib import Path

from sidekick.constants import UNDO_DISABLED_HOME, UNDO_DISABLED_UNSAFE
from sidekick.core.setup.base import BaseSetup
from sidekick.core.state import StateManager
from sidekick.services.undo_service import init_undo_system, is_safe_for_undo
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
            self.state_manager.session.undo_initialized = True
            return

        is_safe, reason = is_safe_for_undo()
        if not is_safe:
            await ui.muted(f"{UNDO_DISABLED_UNSAFE}: {reason}")
            self.state_manager.session.undo_initialized = True
            return

        success = init_undo_system(self.state_manager)
        if not success:
            await ui.warning("Failed to initialize undo system")
        self.state_manager.session.undo_initialized = success

    async def validate(self) -> bool:
        """Validate that undo system was initialized correctly."""
        return self.state_manager.session.undo_initialized
