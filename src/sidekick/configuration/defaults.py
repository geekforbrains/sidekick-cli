"""
Module: sidekick.configuration.defaults

Default configuration values for the Sidekick CLI.
Provides baseline settings for user configuration including API keys,
tool settings, and MCP servers.
"""

from sidekick.constants import GUIDE_FILE_NAME, TOOL_READ_FILE
from sidekick.types import UserConfig

DEFAULT_USER_CONFIG: UserConfig = {
    "default_model": "",
    "env": {
        "ANTHROPIC_API_KEY": "",
        "GEMINI_API_KEY": "",
        "OPENAI_API_KEY": "",
    },
    "settings": {
        "max_retries": 10,
        "tool_ignore": [TOOL_READ_FILE],
        "guide_file": GUIDE_FILE_NAME,
    },
    "mcpServers": {},
}
