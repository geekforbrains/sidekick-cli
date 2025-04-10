import json
import os

from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.validation import ValidationError, Validator

from sidekick import session
from sidekick.config import CONFIG_DIR, CONFIG_FILE, DEFAULT_CONFIG, MODELS
from sidekick.utils import system, telemetry, ui
from sidekick.utils.mcp import init_mcp_servers, start_mcp_servers
from sidekick.utils.undo import init_undo_system


class ModelValidator(Validator):
    """Validate default provider selection"""

    def __init__(self, index):
        # index is the range (non-zero) of the provider list
        # to test against
        self.index = index

    def validate(self, document):
        text = document.text.strip()
        if not text:
            raise ValidationError(message="Provider number cannot be empty")
        elif text and not text.isdigit():
            raise ValidationError(message="Invalid provider number")
        elif text.isdigit():
            number = int(text)
            if number < 0 or number >= self.index:
                raise ValidationError(
                    message="Invalid provider number",
                )


def _load_or_create_config():
    """
    Load user config from ~/.config/sidekick.json,
    creating it with defaults if missing.
    """
    config_created = False
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.is_file():
        with open(CONFIG_FILE, "r") as f:
            session.user_config = json.load(f)
    else:
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        session.user_config = DEFAULT_CONFIG.copy()
        config_created = True
    return config_created


def _set_environment_variables():
    """
    Set environment variables from the config file.
    """
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
    """
    Convert a provider env key to a title string.
    Makes for nicer display in the UI.

    Example:
        ANTHROPIC_API_KEY -> Anthropic API Key
    """
    words = [word.title() for word in key.split("_")]
    return " ".join(words).replace("Api", "API")


async def _step1():
    message = (
        "Welcome to Sidekick!\n"
        "Let's get you setup. First, we'll need to set some environment variables.\n"
        "Skip the ones you don't need."
    )
    ui.panel("Setup", message, border_style=ui.colors.primary)

    prompt_session = PromptSession()
    env_keys = session.user_config["env"].copy()
    for key in env_keys:
        provider = _key_to_title(key)
        val = await prompt_session.prompt_async(f"  {provider}: ", is_password=True)
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
    prompt_session = PromptSession()
    choice = int(
        await prompt_session.prompt_async(
            "  Default model (#): ",
            validator=ModelValidator(len(model_ids)),
        )
    )
    session.user_config["default_model"] = model_ids[choice]


async def _step3():
    """Setup MCP servers"""
    message = (
        "You can configure MCP servers in your ~/.config/sidekick.json file.\n\n"
        "For example:\n\n"
        '"mcpServers": {\n'
        '  "fetch": {\n'
        '    "command": "uvx",\n'
        '    "args": ["mcp-server-fetch"]\n'
        "  }\n"
        "}"
    )
    ui.panel("MCP Servers", message, border_style=ui.colors.primary)


async def _onboarding():
    await _step1()
    await _step2()
    await _step3()

    message = "Config saved to: [bold]~/.config/sidekick.json[/bold]"
    ui.panel("Finished", message, top=0, border_style=ui.colors.success)

    # Save the updated configs
    with open(CONFIG_FILE, "w") as f:
        json.dump(session.user_config, f, indent=4)


def setup_telemetry():
    """Setup telemetry for capturing exceptions and errors"""
    if not session.telemetry_enabled:
        ui.status("Telemetry disabled, skipping")
        return

    ui.status("Setting up telemetry")
    telemetry.setup()


async def setup_config():
    """Setup configuration and environment variables"""
    ui.status("Setting up config")

    # Initialize device ID
    session.device_id = system.get_device_id()

    # Load returns true if new config created (and requires onboarding)
    if _load_or_create_config():
        await _onboarding()

    _set_environment_variables()

    # Set the current model from user config
    if not session.user_config.get("default_model"):
        raise ValueError("No default model found in config at [bold]~/.config/sidekick.json")
    session.current_model = session.user_config["default_model"]


async def setup_mcp():
    """Initialize and setup MCP servers"""
    ui.status("Setting up MCP servers")
    session.mcp_servers = init_mcp_servers(session.user_config.get("mcpServers", {}))
    await start_mcp_servers()


def setup_undo():
    """Initialize the undo system"""
    ui.status("Initializing undo system")
    session.undo_initialized = init_undo_system()


def setup_agent(agent):
    """Initialize the agent with the current model"""
    if agent is not None:
        ui.status(f"Initializing Agent({session.current_model})")
        agent.agent = agent.get_agent()


async def setup(agent=None):
    """
    Setup Sidekick on startup.

    Args:
        agent: An optional MainAgent instance to initialize
    """
    setup_telemetry()
    await setup_config()
    await setup_mcp()
    setup_undo()
    setup_agent(agent)
