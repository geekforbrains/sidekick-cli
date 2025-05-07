import json
import os

from sidekick import session, ui
from sidekick.config import CONFIG_DIR, CONFIG_FILE, DEFAULT_CONFIG, MODELS
from sidekick.exceptions import SidekickConfigError
from sidekick.utils import system, telemetry, user_config
from sidekick.utils.undo import init_undo_system


def _load_or_create_config():
    """
    Load user config from ~/.config/sidekick.json,
    creating it with defaults if missing.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    loaded_config = user_config.load_config()
    if loaded_config:
        session.user_config = loaded_config
        return False
    else:
        session.user_config = DEFAULT_CONFIG.copy()
        user_config.save_config()
        return True


def _set_environment_variables():
    """Set environment variables from the config file."""
    if "env" not in session.user_config or not isinstance(session.user_config["env"], dict):
        session.user_config["env"] = {}

    env_dict = session.user_config["env"]
    for key, value in env_dict.items():
        if not isinstance(value, str):
            ui.warning(f"Invalid env value in config: {key}")
            continue
        value = value.strip()
        if value:
            os.environ[key] = value


def _key_to_title(key):
    """Convert a provider env key to a title string."""
    words = [word.title() for word in key.split("_")]
    return " ".join(words).replace("Api", "API")


async def _step1():
    message = (
        "Welcome to Sidekick!\n"
        "Let's get you setup. First, we'll need to set some environment variables.\n"
        "Skip the ones you don't need."
    )
    ui.panel("Setup", message, border_style=ui.colors.primary)
    env_keys = session.user_config["env"].copy()
    for key in env_keys:
        provider = _key_to_title(key)
        val = await ui.input(session="step1", pretext=f"  {provider}: ", is_password=True)
        val = val.strip()
        if val:
            session.user_config["env"][key] = val


async def _step2():
    message = "Which model would you like to use by default?\n\n"

    model_ids = list(MODELS.keys())
    for index, model_id in enumerate(model_ids):
        message += f"  {index} - {model_id}\n"
    message = message.strip()

    ui.panel("Default Model", message, border_style=ui.colors.primary)
    choice = await ui.input(
        session="step2",
        pretext="  Default model (#): ",
        validator=ui.ModelValidator(len(model_ids)),
    )
    session.user_config["default_model"] = model_ids[choice]


async def _onboarding():
    initial_config = json.dumps(session.user_config, sort_keys=True)

    await _step1()

    # Only continue if at least one API key was provided
    env = session.user_config.get("env", {})
    has_api_key = any(key.endswith("_API_KEY") and env.get(key) for key in env)

    if has_api_key:
        if not session.user_config.get("default_model"):
            await _step2()

        # Compare configs to see if anything changed
        current_config = json.dumps(session.user_config, sort_keys=True)
        if initial_config != current_config:
            if user_config.save_config():
                message = f"Config saved to: [bold]{CONFIG_FILE}[/bold]"
                ui.panel("Finished", message, top=0, border_style=ui.colors.success)
            else:
                ui.error("Failed to save configuration.")
    else:
        ui.panel(
            "Setup canceled", "At least one API key is required.", border_style=ui.colors.warning
        )


def _setup_telemetry():
    """Setup telemetry for capturing exceptions and errors"""
    if not session.telemetry_enabled:
        ui.info("Telemetry disabled, skipping")
        return

    ui.info("Setting up telemetry")
    telemetry.setup()


async def _setup_config(run_setup):
    """Setup configuration and environment variables"""
    ui.info("Setting up config")

    session.device_id = system.get_device_id()
    loaded_config = user_config.load_config()

    if loaded_config and not run_setup:
        ui.muted(f"Loading config from: {CONFIG_FILE}")
        session.user_config = loaded_config
    else:
        if run_setup:
            ui.muted("Running setup process, resetting config")
        else:
            ui.muted("No user configuration found, running setup")
        session.user_config = DEFAULT_CONFIG.copy()
        user_config.save_config()  # Save the default config initially
        await _onboarding()

    if not session.user_config.get("default_model"):
        raise SidekickConfigError(
            (
                f"No default model found in config at [bold]{CONFIG_FILE}[/bold]\n\n"
                "Run [code]sidekick --setup[/code] to rerun the setup process."
            )
        )

    session.current_model = session.user_config["default_model"]


def _setup_undo():
    """Initialize the undo system"""
    ui.info("Initializing undo system")
    session.undo_initialized = init_undo_system()


def _setup_agent(agent):
    """Initialize the agent with the current model"""
    if agent is not None:
        ui.info(f"Initializing Agent({session.current_model})")
        agent.agent = agent.get_agent()


async def setup(run_setup):
    """
    Setup Sidekick on startup.

    Args:
        run_setup (bool): If True, force run the setup process, resetting current config.
    """
    _setup_telemetry()
    await _setup_config(run_setup)
    _set_environment_variables()
    _setup_undo()
