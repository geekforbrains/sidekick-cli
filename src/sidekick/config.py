from pathlib import Path

VERSION = "0.3.0"
NAME = "Sidekick"
GUIDE_FILE = f"{NAME.upper()}.md"
MODELS = {
    "anthropic:claude-3-7-sonnet-latest": {
        "pricing": {
            "input": 3.00,
            "cached_input": 1.50,
            "output": 15.00,
        }
    },
    "google-gla:gemini-2.0-flash": {
        "pricing": {
            "input": 0.10,
            "cached_input": 0.025,
            "output": 0.40,
        }
    },
    "google-gla:gemini-2.5-pro-exp-03-25": {
        # No public pricing yet, so use 2.0-flash numbers
        "pricing": {
            "input": 0.10,
            "cached_input": 0.025,
            "output": 0.40,
        }
    },
    "openai:gpt-4o": {
        "pricing": {
            "input": 2.50,
            "cached_input": 1.25,
            "output": 10.00,
        }
    },
    "openai:o3-mini": {
        "pricing": {
            "input": 1.10,
            "cached_input": 0.55,
            "output": 4.40,
        }
    },
}

CONFIG_DIR = Path.home() / ".config"
CONFIG_FILE = CONFIG_DIR / "sidekick.json"
DEFAULT_CONFIG = {
    "default_model": "",
    "env": {
        "ANTHROPIC_API_KEY": "",
        "GEMINI_API_KEY": "",
        "OPENAI_API_KEY": "",
    },
    "settings": {
        "max_retries": 10,
        "tool_ignore": [
            "read_file",
        ],
    },
    "mcpServers": {},
}

# For filtering tool calls, showing statuses etc.
INTERNAL_TOOLS = [
    "read_file",
    "run_command",
    "update_file",
    "write_file",
]
