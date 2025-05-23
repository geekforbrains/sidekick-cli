from typing import Any, Optional

from sidekick.core.setup import (AgentSetup, ConfigSetup, EnvironmentSetup, SetupCoordinator,
                                 TelemetrySetup, UndoSetup)
from sidekick.core.state import StateManager


async def setup(run_setup: bool, state_manager: StateManager) -> None:
    """
    Setup Sidekick on startup using the new setup coordinator.

    Args:
        run_setup (bool): If True, force run the setup process, resetting current config.
        state_manager (StateManager): The state manager instance.
    """
    coordinator = SetupCoordinator(state_manager)

    # Register setup steps in order
    coordinator.register_step(TelemetrySetup(state_manager))
    coordinator.register_step(ConfigSetup(state_manager))
    coordinator.register_step(EnvironmentSetup(state_manager))
    coordinator.register_step(UndoSetup(state_manager))

    # Run all setup steps
    await coordinator.run_setup(force_setup=run_setup)


async def setup_agent(agent: Optional[Any], state_manager: StateManager) -> None:
    """
    Setup the agent separately.

    This is called from other parts of the codebase when an agent needs to be initialized.

    Args:
        agent: The agent instance to initialize.
        state_manager (StateManager): The state manager instance.
    """
    if agent is not None:
        agent_setup = AgentSetup(state_manager, agent)
        if await agent_setup.should_run():
            await agent_setup.execute()
            if not await agent_setup.validate():
                raise RuntimeError("Agent setup failed validation")
