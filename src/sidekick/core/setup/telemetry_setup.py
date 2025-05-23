from sidekick.core.setup.base import BaseSetup
from sidekick.core.state import StateManager
from sidekick.services import telemetry


class TelemetrySetup(BaseSetup):
    """Setup step for telemetry initialization."""

    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)

    @property
    def name(self) -> str:
        return "Telemetry"

    async def should_run(self, force_setup: bool = False) -> bool:
        """Telemetry should run if enabled, regardless of force_setup."""
        return self.state_manager.session.telemetry_enabled

    async def execute(self, force_setup: bool = False) -> None:
        """Setup telemetry for capturing exceptions and errors."""
        telemetry.setup(self.state_manager)

    async def validate(self) -> bool:
        """Validate that telemetry was set up correctly."""
        # For now, we assume telemetry setup always succeeds
        # In the future, we could check if telemetry is properly initialized
        return True
