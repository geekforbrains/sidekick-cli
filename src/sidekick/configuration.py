"""
Module: sidekick.configuration

Unified configuration management for the Sidekick CLI.
Consolidates all configuration-related functionality including settings,
model registry, defaults, and user configuration file management.
"""

import json
from json import JSONDecodeError
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from sidekick.constants import (APP_NAME, APP_VERSION, CONFIG_FILE_NAME, GUIDE_FILE_NAME,
                                TOOL_READ_FILE, TOOL_RUN_COMMAND, TOOL_UPDATE_FILE, TOOL_WRITE_FILE)
from sidekick.exceptions import ConfigurationError
from sidekick.types import ConfigFile, ConfigPath, MCPServers, ModelConfig, ModelName, ModelPricing
from sidekick.types import ModelRegistry as ModelRegistryType
from sidekick.types import ToolName, UserConfig

if TYPE_CHECKING:
    from sidekick.types import SessionState


# Default configuration values
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


class PathConfig:
    """Configuration for application file paths."""

    def __init__(self):
        self.config_dir: ConfigPath = Path.home() / ".config"
        self.config_file: ConfigFile = self.config_dir / CONFIG_FILE_NAME


class ApplicationSettings:
    """Application settings and configuration."""

    def __init__(self):
        self.version = APP_VERSION
        self.name = APP_NAME
        self.guide_file = f"{self.name.upper()}.md"
        self.paths = PathConfig()
        self.internal_tools: list[ToolName] = [
            TOOL_READ_FILE,
            TOOL_RUN_COMMAND,
            TOOL_UPDATE_FILE,
            TOOL_WRITE_FILE,
        ]


class ModelRegistry:
    """Registry for AI models and their configurations."""

    def __init__(self):
        self._models = self._load_default_models()

    def _load_default_models(self) -> ModelRegistryType:
        return {
            "anthropic:claude-opus-4-20250514": ModelConfig(
                pricing=ModelPricing(input=3.00, cached_input=1.50, output=15.00)
            ),
            "anthropic:claude-sonnet-4-20250514": ModelConfig(
                pricing=ModelPricing(input=3.00, cached_input=1.50, output=15.00)
            ),
            "anthropic:claude-3-7-sonnet-latest": ModelConfig(
                pricing=ModelPricing(input=3.00, cached_input=1.50, output=15.00)
            ),
            "google-gla:gemini-2.0-flash": ModelConfig(
                pricing=ModelPricing(input=0.10, cached_input=0.025, output=0.40)
            ),
            "google-gla:gemini-2.5-flash-preview-05-20": ModelConfig(
                pricing=ModelPricing(input=0.15, cached_input=0.025, output=0.60)
            ),
            "google-gla:gemini-2.5-pro-preview-05-06": ModelConfig(
                pricing=ModelPricing(input=1.25, cached_input=0.025, output=10.00)
            ),
            "openai:gpt-4.1": ModelConfig(
                pricing=ModelPricing(input=2.00, cached_input=0.50, output=8.00)
            ),
            "openai:gpt-4.1-mini": ModelConfig(
                pricing=ModelPricing(input=0.40, cached_input=0.10, output=1.60)
            ),
            "openai:gpt-4.1-nano": ModelConfig(
                pricing=ModelPricing(input=0.10, cached_input=0.025, output=0.40)
            ),
            "openai:gpt-4o": ModelConfig(
                pricing=ModelPricing(input=2.50, cached_input=1.25, output=10.00)
            ),
            "openai:o3": ModelConfig(
                pricing=ModelPricing(input=10.00, cached_input=2.50, output=40.00)
            ),
            "openai:o3-mini": ModelConfig(
                pricing=ModelPricing(input=1.10, cached_input=0.55, output=4.40)
            ),
        }

    def get_model(self, name: ModelName) -> ModelConfig:
        return self._models.get(name)

    def list_models(self) -> ModelRegistryType:
        return self._models.copy()

    def list_model_ids(self) -> list[ModelName]:
        return list(self._models.keys())


# User configuration file management functions


def load_config() -> Optional[UserConfig]:
    """Load user config from file."""
    app_settings = ApplicationSettings()
    try:
        with open(app_settings.paths.config_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except JSONDecodeError:
        raise ConfigurationError(f"Invalid JSON in config file at {app_settings.paths.config_file}")
    except Exception as e:
        raise ConfigurationError(e)


def save_config(session: "SessionState") -> bool:
    """Save user config to file."""
    app_settings = ApplicationSettings()
    try:
        with open(app_settings.paths.config_file, "w") as f:
            json.dump(session.user_config, f, indent=4)
        return True
    except Exception:
        return False


def get_mcp_servers(session: "SessionState") -> MCPServers:
    """Retrieve MCP server configurations from user config."""
    return session.user_config.get("mcpServers", [])


def set_default_model(model_name: ModelName, session: "SessionState") -> bool:
    """Set the default model in the user config and save."""
    session.user_config["default_model"] = model_name
    return save_config(session)
