import json
from pathlib import Path

from sidekick.configuration.defaults import DEFAULT_USER_CONFIG
from sidekick.configuration.models import ModelRegistry
from sidekick.core.setup.base import BaseSetup
from sidekick.core.state import StateManager
from sidekick.exceptions import SidekickConfigError
from sidekick.ui import console as ui
from sidekick.utils import system, user_config
from sidekick.utils.text_utils import key_to_title


class ConfigSetup(BaseSetup):
    """Setup step for configuration and onboarding."""

    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.config_dir = Path.home() / ".config"
        self.config_file = self.config_dir / "sidekick.json"
        self.model_registry = ModelRegistry()

    @property
    def name(self) -> str:
        return "Configuration"

    async def should_run(self, force_setup: bool = False) -> bool:
        """Config setup should always run to load and merge configuration."""
        return True

    async def execute(self, force_setup: bool = False) -> None:
        """Setup configuration and run onboarding if needed."""
        self.state_manager.session.device_id = system.get_device_id()
        loaded_config = user_config.load_config()

        if loaded_config and not force_setup:
            await ui.muted(f"Loading config from: {self.config_file}")
            # Merge loaded config with defaults to ensure all required keys exist
            self.state_manager.session.user_config = self._merge_with_defaults(loaded_config)
        else:
            if force_setup:
                await ui.muted("Running setup process, resetting config")
            else:
                await ui.muted("No user configuration found, running setup")
            self.state_manager.session.user_config = DEFAULT_USER_CONFIG.copy()
            user_config.save_config(self.state_manager)  # Save the default config initially
            await self._onboarding()

        if not self.state_manager.session.user_config.get("default_model"):
            raise SidekickConfigError(
                (
                    f"No default model found in config at [bold]{self.config_file}[/bold]\n\n"
                    "Run [code]sidekick --setup[/code] to rerun the setup process."
                )
            )

        self.state_manager.session.current_model = self.state_manager.session.user_config[
            "default_model"
        ]

    async def validate(self) -> bool:
        """Validate that configuration is properly set up."""
        # Check that we have a user config
        if not self.state_manager.session.user_config:
            return False

        # Check that we have a default model
        if not self.state_manager.session.user_config.get("default_model"):
            return False

        # Check that the default model is valid
        default_model = self.state_manager.session.user_config["default_model"]
        if not self.model_registry.get_model(default_model):
            return False

        return True

    def _merge_with_defaults(self, loaded_config):
        """Merge loaded config with defaults to ensure all required keys exist."""
        # Start with loaded config if available, otherwise use defaults
        if loaded_config:
            merged = loaded_config.copy()

            # Add missing top-level keys from defaults
            for key, default_value in DEFAULT_USER_CONFIG.items():
                if key not in merged:
                    merged[key] = default_value

            return merged
        else:
            return DEFAULT_USER_CONFIG.copy()

    async def _onboarding(self):
        """Run the onboarding process for new users."""
        initial_config = json.dumps(self.state_manager.session.user_config, sort_keys=True)

        await self._step1_api_keys()

        # Only continue if at least one API key was provided
        env = self.state_manager.session.user_config.get("env", {})
        has_api_key = any(key.endswith("_API_KEY") and env.get(key) for key in env)

        if has_api_key:
            if not self.state_manager.session.user_config.get("default_model"):
                await self._step2_default_model()

            # Compare configs to see if anything changed
            current_config = json.dumps(self.state_manager.session.user_config, sort_keys=True)
            if initial_config != current_config:
                if user_config.save_config(self.state_manager):
                    message = f"Config saved to: [bold]{self.config_file}[/bold]"
                    await ui.panel("Finished", message, top=0, border_style=ui.colors.success)
                else:
                    await ui.error("Failed to save configuration.")
        else:
            await ui.panel(
                "Setup canceled",
                "At least one API key is required.",
                border_style=ui.colors.warning,
            )

    async def _step1_api_keys(self):
        """Onboarding step 1: Collect API keys."""
        message = (
            "Welcome to Sidekick!\n"
            "Let's get you setup. First, we'll need to set some environment variables.\n"
            "Skip the ones you don't need."
        )
        await ui.panel("Setup", message, border_style=ui.colors.primary)
        env_keys = self.state_manager.session.user_config["env"].copy()
        for key in env_keys:
            provider = key_to_title(key)
            val = await ui.input("step1", pretext=f"  {provider}: ", is_password=True)
            val = val.strip()
            if val:
                self.state_manager.session.user_config["env"][key] = val

    async def _step2_default_model(self):
        """Onboarding step 2: Select default model."""
        message = "Which model would you like to use by default?\n\n"

        model_ids = self.model_registry.list_model_ids()
        for index, model_id in enumerate(model_ids):
            message += f"  {index} - {model_id}\n"
        message = message.strip()

        await ui.panel("Default Model", message, border_style=ui.colors.primary)
        choice = await ui.input(
            "step2",
            pretext="  Default model (#): ",
            validator=ui.ModelValidator(len(model_ids)),
        )
        self.state_manager.session.user_config["default_model"] = model_ids[int(choice)]
