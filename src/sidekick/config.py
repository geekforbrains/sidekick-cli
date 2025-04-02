import os
import sys
from pathlib import Path

NAME = "Sidekick"

# Determine if we're running in a development environment
# Check if we're running from source or as an installed package
IS_DEV = os.path.exists(os.path.join(os.path.dirname(__file__), '..', '..', 'pyproject.toml'))
MODELS = [
    "anthropic:claude-3-7-sonnet-latest",
    "google-gla:gemini-2.0-flash",
    "google-gla:gemini-2.5-pro-exp-03-25",
    "openai:gpt-4o",
    "openai:o3-mini",
]
MODEL_PRICING = {
    # No public pricing yet, so use 2.0-flash numbers
    "google-gla:gemini-2.5-pro-exp-03-25": {
        "input": 0.10,
        "cached_input": 0.025,
        "output": 0.40,
    },
    "google-gla:gemini-2.0-flash": {
        "input": 0.10,
        "cached_input": 0.025,
        "output": 0.40,
    },
    "openai:o3-mini": {
        "input": 1.10,
        "cached_input": 0.55,
        "output": 4.40,
    },
    "openai:gpt-4o": {
        "input": 2.50,
        "cached_input": 1.25,
        "output": 10.00,
    },
    "anthropic:claude-3-7-sonnet-latest": {
        "input": 3.00,
        "cached_input": 1.50,
        "output": 15.00,
    },
}

CONFIG_DIR = Path.home() / ".config"
CONFIG_FILE = CONFIG_DIR / "sidekick.json"
DEFAULT_CONFIG = {
    "default_model": "",
    "env": {
        "providers": {
            "ANTHROPIC_API_KEY": "",
            "GEMINI_API_KEY": "",
            "OPENAI_API_KEY": "",
        },
        "tools": {
            "BRAVE_SEARCH_API_KEY": "",
        },
    },
    "settings": {
        "max_retries": 10,
    },
}
