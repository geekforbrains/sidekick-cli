import asyncio
import json
import os
import subprocess
import sys

from prompt_toolkit import prompt
from prompt_toolkit.validation import ValidationError, Validator

from sidekick import session
from sidekick.config import CONFIG_DIR, CONFIG_FILE, DEFAULT_CONFIG, MODELS
from sidekick.utils import system, ui


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


def _set_environment_variables():
    """
    Set environment variables from the config file.
    """
    if "env" in session.user_config and isinstance(session.user_config["env"], dict):
        env_dict = session.user_config["env"]

        # Handle provider keys
        if "providers" in env_dict and isinstance(env_dict["providers"], dict):
            for key, value in env_dict["providers"].items():
                if not isinstance(value, str):
                    raise ValueError(f"Invalid provider env value in config: {key}")
                value = value.strip()
                if value:
                    os.environ[key] = value

        # Handle tool keys
        if "tools" in env_dict and isinstance(env_dict["tools"], dict):
            for key, value in env_dict["tools"].items():
                if not isinstance(value, str):
                    raise ValueError(f"Invalid tool env value in config: {key}")
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
    words = [word.title() for word in key.split("_")]
    return " ".join(words).replace("Api", "API")


def _step1():
    message = (
        "Welcome to Sidekick!\n"
        "Let's get you setup. First, we'll need to set some environment variables.\n"
        "Skip the ones you don't need."
    )
    ui.panel("Setup", message, top=0, border_style=ui.colors.primary)

    provider_envs = session.user_config["env"]["providers"].copy()
    for key, _ in provider_envs.items():
        provider = _key_to_title(key)
        val = prompt(f"  {provider}: ", is_password=True)
        val = val.strip()
        if val:
            session.user_config["env"]["providers"][key] = val


def _step2():
    message = "Which model would you like to use by default?\n\n"

    model_ids = list(MODELS.keys())
    for index, model_id in enumerate(model_ids):
        message += f"  {index} - {model_id}\n"
    message = message.strip()

    ui.panel("Default Model", message, border_style=ui.colors.primary)
    choice = int(
        prompt(
            "  Default model (#): ",
            validator=ModelValidator(len(model_ids)),
        )
    )
    session.user_config["default_model"] = model_ids[choice]


def _step3():
    """Setup tools"""
    message = "Now lets setup tools. Skip any you don't want to use"
    ui.panel("Tools", message, border_style=ui.colors.primary)

    # At the moment, we only have Brave search
    brave_api_key = prompt("  Brave Search API Key: ", is_password=True)
    brave_api_key = brave_api_key.strip()

    if brave_api_key:
        session.user_config["env"]["tools"]["BRAVE_SEARCH_API_KEY"] = brave_api_key


def _onboarding():
    _step1()
    _step2()
    _step3()

    message = "Config saved to: [bold]~/.config/sidekick.json[/bold]"
    ui.panel("Finished", message, border_style=ui.colors.success)

    # Save the updated configs
    with open(CONFIG_FILE, "w") as f:
        json.dump(session.user_config, f, indent=4)


def _check_playwright():
    """
    Check if Playwright is properly installed and configured.
    Return True if installation is needed.
    """
    try:
        # Check if the module is importable
        # Try a simple browser launch to see if binaries are installed
        from playwright.async_api import async_playwright

        async def test_playwright():
            try:
                async with async_playwright() as p:
                    # Just try to launch and close browser quickly
                    browser = await p.chromium.launch(headless=True)
                    await browser.close()
                return True
            except Exception:
                return False

        if not asyncio.run(test_playwright()):
            message = (
                "Playwright is installed but browser binaries are missing.\n"
                "Would you like to install them now? (y/n)"
            )
            ui.panel("Playwright Setup", message, border_style=ui.colors.warning)
            choice = prompt("  Install Playwright browsers? (y/n): ")
            if choice.lower().startswith("y"):
                ui.status("Installing Playwright browsers")
                ui.line()
                try:
                    subprocess.run(
                        [sys.executable, "-m", "playwright", "install", "chromium"], check=True
                    )
                    ui.line()
                    ui.success("Playwright browsers installed successfully!")
                except subprocess.CalledProcessError:
                    ui.error(
                        "Failed to install Playwright browsers. You may need to run this manually:"
                    )
                    ui.status("    playwright install")
            else:
                ui.warning("Fetch tool with JavaScript rendering will be unavailable.")

    except ImportError:
        ui.warning(
            "Playwright not installed. Fetch tool will use httpx only (no JavaScript support)."
        )


def setup():
    """
    Setup user config file if needed, with onboarding questions. Load user
    config and set environment variables.

    """
    # Initialize device ID
    session.device_id = system.get_device_id()

    # Load returns true if new config created (and requires onboarding)
    if _load_or_create_config():
        _onboarding()

    _set_environment_variables()

    # Check Playwright installation
    _check_playwright()
