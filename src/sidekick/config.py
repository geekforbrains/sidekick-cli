"""Configuration management for Sidekick CLI."""

import json
import os
from pathlib import Path
from typing import Any, Dict


class ConfigError(Exception):
    """Base exception for configuration errors."""

    pass


class ConfigValidationError(ConfigError):
    """Raised when config structure is invalid."""

    pass


def get_config_path() -> Path:
    """Get the path to the config file."""
    return Path.home() / ".config" / "sidekick.json"


def config_exists() -> bool:
    """Check if the config file exists."""
    return get_config_path().exists()


def read_config_file() -> Dict[str, Any]:
    """Read and parse the config file.

    Returns:
        dict: Parsed configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        PermissionError: If config file can't be accessed
        json.JSONDecodeError: If config file contains invalid JSON
    """
    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except PermissionError:
        raise PermissionError(f"Cannot access config file at {config_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in config file at {config_path}", e.doc, e.pos)


def validate_config_structure(config: Dict[str, Any]) -> None:
    """Validate the configuration structure.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigValidationError: If required fields are missing or invalid
    """
    if not isinstance(config, dict):
        raise ConfigValidationError("Config must be a JSON object")

    if "default_model" not in config:
        raise ConfigValidationError("Config missing required field 'default_model'")

    if not isinstance(config["default_model"], str):
        raise ConfigValidationError("'default_model' must be a string")

    if "env" not in config:
        raise ConfigValidationError("Config missing required field 'env'")

    if not isinstance(config["env"], dict):
        raise ConfigValidationError("'env' field must be an object")


def parse_mcp_servers(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and validate MCP server configuration.

    Args:
        config: Full configuration dictionary

    Returns:
        dict: MCP servers configuration (may be empty)

    Raises:
        ConfigValidationError: If mcpServers field is present but invalid
    """
    if "mcpServers" not in config:
        return {}

    mcp_servers = config["mcpServers"]

    if not isinstance(mcp_servers, dict):
        raise ConfigValidationError("'mcpServers' field must be an object")

    # Basic validation of server entries
    for key, server_config in mcp_servers.items():
        if not isinstance(server_config, dict):
            raise ConfigValidationError(f"MCP server '{key}' configuration must be an object")

        if "command" not in server_config:
            raise ConfigValidationError(f"MCP server '{key}' missing required field 'command'")

        if not isinstance(server_config["command"], str):
            raise ConfigValidationError(f"MCP server '{key}' field 'command' must be a string")

        if "args" not in server_config:
            raise ConfigValidationError(f"MCP server '{key}' missing required field 'args'")

        if not isinstance(server_config["args"], list):
            raise ConfigValidationError(f"MCP server '{key}' field 'args' must be an array")

        if len(server_config["args"]) < 1:
            raise ConfigValidationError(
                f"MCP server '{key}' field 'args' must contain at least one argument"
            )

        if "env" in server_config and not isinstance(server_config["env"], dict):
            raise ConfigValidationError(f"MCP server '{key}' field 'env' must be an object")

    return mcp_servers


def set_env_vars(env_dict: Dict[str, str]) -> None:
    """Set environment variables from config.

    Args:
        env_dict: Dictionary of environment variables to set
    """
    for key, value in env_dict.items():
        if value and isinstance(value, str):
            os.environ[key] = value
