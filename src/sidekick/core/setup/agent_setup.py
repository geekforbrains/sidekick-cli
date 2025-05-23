from typing import Any, Optional

from sidekick.core.setup.base import BaseSetup
from sidekick.core.state import StateManager
from sidekick.ui import console as ui


class AgentSetup(BaseSetup):
    """Setup step for agent initialization."""

    def __init__(self, state_manager: StateManager, agent: Optional[Any] = None):
        super().__init__(state_manager)
        self.agent = agent

    @property
    def name(self) -> str:
        return "Agent"

    async def should_run(self, force_setup: bool = False) -> bool:
        """Agent setup should run if an agent is provided."""
        return self.agent is not None

    async def execute(self, force_setup: bool = False) -> None:
        """Initialize the agent with the current model."""
        if self.agent is not None:
            await ui.info(f"Initializing Agent({self.state_manager.session.current_model})")
            self.agent.agent = self.agent.get_agent()

    async def validate(self) -> bool:
        """Validate that agent was initialized correctly."""
        if self.agent is None:
            return True  # No agent to validate

        # Check if agent was initialized
        return hasattr(self.agent, "agent") and self.agent.agent is not None
