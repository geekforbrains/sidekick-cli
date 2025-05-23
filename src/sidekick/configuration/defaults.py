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
        "tool_ignore": ["read_file"],
        "guide_file": "SIDEKICK.md",
    },
    "mcpServers": {},
}
