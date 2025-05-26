"""
Module: sidekick.setup

Package setup and metadata configuration for the Sidekick CLI.
Provides high-level setup functions for initializing the application and its agents.
"""

import os
from pathlib import Path

from sidekick.configuration.defaults import DEFAULT_USER_CONFIG
from sidekick.configuration.models import ModelRegistry
from sidekick.constants import (APP_NAME, CONFIG_FILE_NAME, UI_COLORS, UNDO_DISABLED_HOME,
                                UNDO_DISABLED_UNSAFE)
from sidekick.core.state import StateManager
from sidekick.exceptions import ConfigurationError
from sidekick.services import telemetry
from sidekick.services.undo_service import init_undo_system, is_safe_for_undo
from sidekick.types import EnvConfig
from sidekick.ui.input import input
from sidekick.ui.output import muted, warning
from sidekick.ui.panels import error
from sidekick.ui.panels import panel
from sidekick.ui.validators import ModelValidator
from sidekick.utils import system, user_configuration
from sidekick.utils.text_utils import key_to_title


async def setup(run_setup: bool, state_manager: StateManager) -> None:
    """
    Setup Sidekick on startup.

    Args:
        run_setup (bool): If True, force run the setup process, resetting current config.
        state_manager (StateManager): The state manager instance.
    """
    try:
        # Step 1: Setup telemetry
        if state_manager.session.telemetry_enabled:
            telemetry.setup(state_manager)

        # Step 2: Setup configuration
        await _setup_config(run_setup, state_manager)

        # Step 3: Setup environment variables
        await _setup_environment(state_manager)

        # Step 4: Setup undo system
        await _setup_undo(state_manager)

    except Exception as e:
        await error(f"Setup failed: {str(e)}")
        raise


async def _setup_config(force_setup: bool, state_manager: StateManager) -> None:
    """Setup configuration and run onboarding if needed."""
    config_dir = Path.home() / ".config"
    config_file = config_dir / CONFIG_FILE_NAME
    model_registry = ModelRegistry()

    state_manager.session.device_id = system.get_device_id()
    loaded_config = user_configuration.load_config()

    if loaded_config and not force_setup:
        await muted(f"Loading config from: {config_file}")
        # Merge loaded config with defaults to ensure all required keys exist
        state_manager.session.user_config = _merge_with_defaults(loaded_config)
    else:
        if force_setup:
            await muted("Running setup process, resetting config")
        else:
            await muted("No user configuration found, running setup")
        state_manager.session.user_config = DEFAULT_USER_CONFIG.copy()
        user_configuration.save_config(state_manager)  # Save the default config initially
        await _onboarding(state_manager, config_file, model_registry)

    if not state_manager.session.user_config.get("default_model"):
        raise ConfigurationError(
            (
                f"No default model found in config at [bold]{config_file}[/bold]\n\n"
                "Run [code]sidekick --setup[/code] to rerun the setup process."
            )
        )

    # Check if the configured model still exists
    default_model = state_manager.session.user_config["default_model"]
    if not model_registry.get_model(default_model):
        await panel(
            "Model Not Found",
            f"The configured model '[bold]{default_model}[/bold]' is no longer available.\n"
            "Please select a new default model.",
            border_style=UI_COLORS["warning"],
        )
        await _select_default_model(state_manager, model_registry)
        user_configuration.save_config(state_manager)

    state_manager.session.current_model = state_manager.session.user_config["default_model"]


async def _setup_environment(state_manager: StateManager) -> None:
    """Set environment variables from the config file."""
    if "env" not in state_manager.session.user_config or not isinstance(
        state_manager.session.user_config["env"], dict
    ):
        state_manager.session.user_config["env"] = {}

    env_dict: EnvConfig = state_manager.session.user_config["env"]
    env_set_count = 0

    for key, value in env_dict.items():
        if not isinstance(value, str):
            await warning(f"Invalid env value in config: {key}")
            continue
        value = value.strip()
        if value:
            os.environ[key] = value
            env_set_count += 1

    if env_set_count > 0:
        await muted(f"Set {env_set_count} environment variable(s)")


async def _setup_undo(state_manager: StateManager) -> None:
    """Initialize the undo system."""
    if state_manager.session.undo_initialized:
        return

    cwd = Path.cwd()
    home_dir = Path.home()

    if cwd == home_dir:
        await muted(UNDO_DISABLED_HOME)
        state_manager.session.undo_initialized = True
        return

    is_safe, reason = is_safe_for_undo()
    if not is_safe:
        await muted(f"{UNDO_DISABLED_UNSAFE}: {reason}")
        state_manager.session.undo_initialized = True
        return

    success = init_undo_system(state_manager)
    if not success:
        await warning("Failed to initialize undo system")
    state_manager.session.undo_initialized = success


def _merge_with_defaults(loaded_config):
    """Merge loaded config with defaults to ensure all required keys exist."""
    if loaded_config:
        merged = loaded_config.copy()
        # Add missing top-level keys from defaults
        for key, default_value in DEFAULT_USER_CONFIG.items():
            if key not in merged:
                merged[key] = default_value
        return merged
    else:
        return DEFAULT_USER_CONFIG.copy()


async def _onboarding(state_manager: StateManager, config_file, model_registry: ModelRegistry):
    """Run the onboarding process for new users."""
    import json

    initial_config = json.dumps(state_manager.session.user_config, sort_keys=True)

    await _collect_api_keys(state_manager)

    # Only continue if at least one API key was provided
    env = state_manager.session.user_config.get("env", {})
    has_api_key = any(key.endswith("_API_KEY") and env.get(key) for key in env)

    if has_api_key:
        if not state_manager.session.user_config.get("default_model"):
            await _select_default_model(state_manager, model_registry)

        # Compare configs to see if anything changed
        current_config = json.dumps(state_manager.session.user_config, sort_keys=True)
        if initial_config != current_config:
            if user_configuration.save_config(state_manager):
                message = f"Config saved to: [bold]{config_file}[/bold]"
                await panel("Finished", message, top=0, border_style=UI_COLORS["success"])
            else:
                await error("Failed to save configuration.")
    else:
        await panel(
            "Setup canceled",
            "At least one API key is required.",
            border_style=UI_COLORS["warning"],
        )


async def _collect_api_keys(state_manager: StateManager):
    """Onboarding step 1: Collect API keys."""
    message = (
        f"Welcome to {APP_NAME}!\n"
        "Let's get you setup. First, we'll need to set some environment variables.\n"
        "Skip the ones you don't need."
    )
    await panel("Setup", message, border_style=UI_COLORS["primary"])
    env_keys = state_manager.session.user_config["env"].copy()
    for key in env_keys:
        provider = key_to_title(key)
        val = await input(
            "step1",
            pretext=f"  {provider}: ",
            is_password=True,
            state_manager=state_manager,
        )
        val = val.strip()
        if val:
            state_manager.session.user_config["env"][key] = val


async def _select_default_model(state_manager: StateManager, model_registry: ModelRegistry):
    """Onboarding step 2: Select default model."""
    message = "Which model would you like to use by default?\n\n"

    model_ids = model_registry.list_model_ids()
    for index, model_id in enumerate(model_ids):
        message += f"  {index} - {model_id}\n"
    message = message.strip()

    await panel("Default Model", message, border_style=UI_COLORS["primary"])
    choice = await input(
        "step2",
        pretext="  Default model (#): ",
        validator=ModelValidator(len(model_ids)),
        state_manager=state_manager,
    )
    state_manager.session.user_config["default_model"] = model_ids[int(choice)]
