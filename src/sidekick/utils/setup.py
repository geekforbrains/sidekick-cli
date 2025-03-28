import json
import os
import sys

from rich import print

from sidekick import session
from sidekick.config import CONFIG_DIR, CONFIG_FILE, DEFAULT_CONFIG
from sidekick.utils import ui


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
    Convert a key to a title string.
    """
    return key.split("_")[0].title()


def onboarding():
    from prompt_toolkit import prompt
    from prompt_toolkit.validation import Validator, ValidationError

    message1 = (
        "Welcome to Sidekick!\n"
        "Let's get you setup. First, we'll need to set some environment variables.\n"
        "Skip the ones you don't need."
    )
    ui._panel("Setup", message1, top=0, border_style=ui.colors.primary)

    envs = {}
    for key, _ in session.user_config["env"].items():
        envs[key] = prompt(f"  {_key_to_title(key)}: ", is_password=True)
    session.user_config["env"] = envs

    # TODO only ask for default if more than one provider set

    message2 = "Which provider would you like to use by default?\n\n"
    index = 1
    for k, v in session.user_config["env"].items():
        if not v:
            continue
        message2 += f"  {index} - {_key_to_title(k)}\n"
        index += 1
    message2 = message2.strip()

    class NumberValidator(Validator):
        def __init__(self, index):
            self.index = index

        def validate(self, document):
            text = document.text

            if text and not text.isdigit():
                i = 0

                # Get index of first non numeric character.
                # We want to move the cursor here.
                for i, c in enumerate(text):
                    if not c.isdigit():
                        break

                raise ValidationError(
                    message="This input contains non-numeric characters",
                    cursor_position=i
                )

    # TODO make custom index map to determine selection

    ui._panel("Setup", message2, border_style=ui.colors.primary)
    # prompt("  Default provider: ")
    number = int(prompt("Choose a provider (#): ", validator=NumberValidator(index)))
    print(f"You said: {number}")



def setup():
    """
    Setup user config file if needed, with onboarding questions. Load user
    config and set environment variables.

    """
    # for now always remove ~/.config/sidekick.json for testing
    if CONFIG_FILE.is_file():
        os.remove(CONFIG_FILE)
    # Load returns true if new config created (and requires onboarding)
    if load_or_create_config():
        onboarding()
    set_environment_variables()
