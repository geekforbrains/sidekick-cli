import os

from sidekick.core.setup.base import BaseSetup
from sidekick.core.state import StateManager
from sidekick.ui import console as ui


class EnvironmentSetup(BaseSetup):
    """Setup step for environment variables."""

    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)

    @property
    def name(self) -> str:
        return "Environment Variables"

    async def should_run(self, force_setup: bool = False) -> bool:
        """Environment setup should always run to set env vars from config."""
        return True

    async def execute(self, force_setup: bool = False) -> None:
        """Set environment variables from the config file."""
        if "env" not in self.state_manager.session.user_config or not isinstance(
            self.state_manager.session.user_config["env"], dict
        ):
            self.state_manager.session.user_config["env"] = {}

        env_dict = self.state_manager.session.user_config["env"]
        env_set_count = 0

        for key, value in env_dict.items():
            if not isinstance(value, str):
                await ui.warning(f"Invalid env value in config: {key}")
                continue
            value = value.strip()
            if value:
                os.environ[key] = value
                env_set_count += 1

        if env_set_count > 0:
            await ui.muted(f"Set {env_set_count} environment variable(s)")

    async def validate(self) -> bool:
        """Validate that environment variables were set correctly."""
        # Check that at least one API key environment variable is set
        env_dict = self.state_manager.session.user_config.get("env", {})
        for key, value in env_dict.items():
            if key.endswith("_API_KEY") and value and value.strip():
                # Check if it was actually set in the environment
                if os.environ.get(key) == value.strip():
                    return True

        # If no API keys are configured, that's still valid
        # (user might be using other auth methods)
        return True
