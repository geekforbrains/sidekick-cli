import json
from json import JSONDecodeError
from typing import TYPE_CHECKING, Optional

from sidekick import config
from sidekick.exceptions import SidekickConfigError
from sidekick.types import MCPServers, ModelName, UserConfig

if TYPE_CHECKING:
    from sidekick.core.state import StateManager


def load_config() -> Optional[UserConfig]:
    """Load user config from file"""
    try:
        with open(config.CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except JSONDecodeError:
        raise SidekickConfigError(f"Invalid JSON in config file at {config.CONFIG_FILE}")
    except Exception as e:
        raise SidekickConfigError(e)


def save_config(state_manager: "StateManager") -> bool:
    """Save user config to file"""
    try:
        with open(config.CONFIG_FILE, "w") as f:
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
