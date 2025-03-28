import json
import os
import sys

from prompt_toolkit import prompt
from prompt_toolkit.validation import ValidationError, Validator

from sidekick import session
from sidekick.config import CONFIG_DIR, CONFIG_FILE, DEFAULT_CONFIG, models
from sidekick.utils import ui


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


def load_or_create_config():
    """
    Load user config from ~/.config/sidekick.json,
    creating it with defaults if missing.
    """
    config_created = False
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if CONFIG_FILE.is_file():
            with open(CONFIG_FILE, "r") as f:
                session.user_config = json.load(f)
        else:
            with open(CONFIG_FILE, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            session.user_config = DEFAULT_CONFIG.copy()
            config_created = True
    except Exception as e:
        # TODO handle UI error nicely
        print(f"FATAL: Failed to initialize configuration system: {e}", file=sys.stderr)
    return config_created


def set_environment_variables():
    """
    Set environment variables from the config file.
    """
    if "env" in session.user_config and isinstance(session.user_config["env"], dict):
        for key, value in session.user_config["env"].items():
            if not isinstance(value, str):
                raise ValueError(f"Invalid env value in config: {key}")
            value = value.strip()
            if value:
                os.environ[key] = value
    else:
        raise ValueError("Invalid env in config. Must be a dictionary.")


def _key_to_title(key):
    """
    Convert a provider env key to a title string.
    Makes for nicer display in the UI.
    """
    return key.split("_")[0].title()


def _step1():
    message = (
        "Welcome to Sidekick!\n"
        "Let's get you setup. First, we'll need to set some environment variables.\n"
        "Skip the ones you don't need."
    )
    ui._panel("Setup", message, top=0, border_style=ui.colors.primary)

    envs = session.user_config["env"].copy()
    for key, _ in envs.items():
        provider = _key_to_title(key)
        val = prompt(f"  {provider}: ", is_password=True)
        val = val.strip()
        if val:
            session.user_config["env"][key] = val


def _step2():
    message = "Which model would you like to use by default?\n\n"

    for index, key in enumerate(models):
        message += f"  {index} - {key}\n"
    message = message.strip()

    ui._panel("Default Model", message, border_style=ui.colors.primary)
    choice = int(
        prompt(
            "  Default model (#): ",
            validator=ModelValidator(len(models)),
        )
    )
    session.user_config["default_model"] = models[choice]


def _step3():
    message = (
        "Config saved to: [bold]~/.config/sidekick.json[/bold]"
    )
    ui._panel("Finished", message, border_style=ui.colors.success)


def onboarding():
    _step1()
    _step2()
    _step3()

    # Save the updated configs
    with open(CONFIG_FILE, "w") as f:
        json.dump(session.user_config, f, indent=4)


def setup():
    """
    Setup user config file if needed, with onboarding questions. Load user
    config and set environment variables.

    """
    # Load returns true if new config created (and requires onboarding)
    if load_or_create_config():
        onboarding()
    set_environment_variables()
