APP_NAME = "Sidekick"
APP_VERSION = "0.5.1"

# Pricing table for supported models (per 1M tokens).
# This is release-time data; override in a future release if pricing changes.
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
    "google-gla:gemini-2.5-pro-preview-03-25": {
        # Pricing per 1M tokens (API pricing, UI is free)
        # Tier: <= 200K tokens. Input: $1.25, Output: $10.00
        # Tier: > 200K tokens. Input: $2.50, Output: $15.00
        # Current config uses lower tier pricing as structure doesn't support tiers.
        "pricing": {
            "input": 1.25,  # Using <=200k tier
            "cached_input": 0.025,  # No price defined for cached input, using input price
            "output": 10.00,  # Using <=200k tier
        }
    },
    "openai:gpt-4.1": {
        "pricing": {
            "input": 2.00,
            "cached_input": 0.50,
            "output": 8.00,
        }
    },
    "openai:gpt-4.1-mini": {
        "pricing": {
            "input": 0.40,
            "cached_input": 0.10,
            "output": 1.60,
        }
    },
    "openai:gpt-4.1-nano": {
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
    "openai:o3": {
        "pricing": {
            "input": 10.00,
            "cached_input": 2.50,
            "output": 40.00,
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

DEFAULT_USER_CONFIG = {
    "default_model": "",
    "env": {
        "ANTHROPIC_API_KEY": "your-anthropic-api-key",
        "OPENAI_API_KEY": "your-openai-api-key",
        "GEMINI_API_KEY": "your-gemini-api-key",
    },
    "mcpServers": {},
    "settings": {
        "allowed_tools": ["read_file"],
        "allowed_commands": [
            "ls",
            "cat",
            "grep",
            "rg",
            "find",
            "pwd",
            "echo",
            "which",
            "head",
            "tail",
            "wc",
            "sort",
            "uniq",
            "diff",
            "tree",
            "file",
            "stat",
            "du",
            "df",
            "ps",
            "top",
            "env",
            "date",
            "whoami",
            "hostname",
            "uname",
            "id",
            "groups",
            "history",
        ],
    },
}
