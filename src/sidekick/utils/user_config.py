import json
from json import JSONDecodeError
from typing import TYPE_CHECKING, Optional

from sidekick.configuration.settings import ApplicationSettings
from sidekick.exceptions import ConfigurationError
from sidekick.types import MCPServers, ModelName, UserConfig

if TYPE_CHECKING:
    from sidekick.core.state import StateManager


def load_config() -> Optional[UserConfig]:
    """Load user config from file"""
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


def save_config(state_manager: "StateManager") -> bool:
    """Save user config to file"""
    app_settings = ApplicationSettings()
    try:
        with open(app_settings.paths.config_file, "w") as f:
            json.dump(state_manager.session.user_config, f, indent=4)
        return True
    except Exception:
        return False


def get_mcp_servers(state_manager: "StateManager") -> MCPServers:
    """Retrieve MCP server configurations from user config"""
    return state_manager.session.user_config.get("mcpServers", [])


def set_default_model(model_name: ModelName, state_manager: "StateManager") -> bool:
    """Set the default model in the user config and save"""
    state_manager.session.user_config["default_model"] = model_name
    return save_config(state_manager)
