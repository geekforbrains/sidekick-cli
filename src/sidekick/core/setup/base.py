"""Module: sidekick.core.setup.base

Base setup step abstraction for the Sidekick CLI initialization process.
Defines the contract that all setup steps must implement.
"""

from abc import ABC, abstractmethod

from sidekick.core.state import StateManager


class BaseSetup(ABC):
    """Base class for all setup steps."""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this setup step."""
        pass

    @abstractmethod
    async def should_run(self, force_setup: bool = False) -> bool:
        """Determine if this setup step should run."""
        pass

    @abstractmethod
    async def execute(self, force_setup: bool = False) -> None:
        """Execute the setup step."""
        pass

    @abstractmethod
    async def validate(self) -> bool:
        """Validate that the setup was successful."""
        pass
