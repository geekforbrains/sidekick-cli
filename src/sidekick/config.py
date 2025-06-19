import json
import os
from pathlib import Path


def load_config():
    """Load configuration from ~/.config/sidekick.json"""
    config_path = Path.home() / ".config" / "sidekick.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at {config_path}\n"
            "Please create a config file with your API keys and default model."
        )

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in config file at {config_path}")

    if "default_model" not in config:
        raise ValueError("Config missing 'default_model' field")

    if "env" not in config:
        raise ValueError("Config missing 'env' field with API keys")

    for key, value in config.get("env", {}).items():
        if value:
            os.environ[key] = value

    return config
