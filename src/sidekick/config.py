"""Configuration management for Sidekick CLI."""

import json
import os
from pathlib import Path
from typing import Any, Dict

from .constants import DEFAULT_USER_CONFIG


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
        ConfigError: If config file doesn't exist or can't be accessed
        ConfigValidationError: If config file contains invalid JSON
    """
    config_path = get_config_path()

    if not config_path.exists():
        raise ConfigError(f"Config file not found at {config_path}")

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except PermissionError as e:
        raise ConfigError(f"Cannot access config file at {config_path}") from e
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"Invalid JSON in config file at {config_path}") from e


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


def update_config_file(updates: Dict[str, Any]) -> None:
    """Update the config file with new values.

    Args:
        updates: Dictionary of updates to apply to the config

    Raises:
        ConfigError: If config file cannot be read or written
    """
    try:
        config = read_config_file()
    except FileNotFoundError:
        raise ConfigError("Config file not found. Please run initial setup first.")

    # Merge updates into existing config
    for key, value in updates.items():
        if isinstance(value, dict) and key in config and isinstance(config[key], dict):
            # For nested dicts, merge instead of replace
            config[key].update(value)
        else:
            config[key] = value

    # Write updated config back to file
    config_path = get_config_path()

    # Ensure the config directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    except (PermissionError, IOError) as e:
        raise ConfigError(f"Failed to write config file: {e}")


def deep_merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, preserving existing values in update.

    Args:
        base: Base dictionary with default values
        update: Dictionary with user values to preserve

    Returns:
        Merged dictionary with all keys from base and values from update where they exist
    """
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def ensure_config_structure() -> Dict[str, Any]:
    """Ensure the config file has all expected keys with defaults for missing ones.

    This function reads the existing config, merges it with the default structure,
    and writes back the updated config if any keys were missing.

    Returns:
        The updated configuration dictionary

    Raises:
        ConfigError: If config file cannot be read or written
    """
    try:
        config = read_config_file()
    except ConfigError:
        raise

    original_config = json.dumps(config, sort_keys=True)
    merged_config = deep_merge_dicts(DEFAULT_USER_CONFIG, config)
    updated_config = json.dumps(merged_config, sort_keys=True)

    if original_config != updated_config:
        try:
            config_path = get_config_path()
            with open(config_path, "w") as f:
                json.dump(merged_config, f, indent=2)
        except (PermissionError, IOError) as e:
            raise ConfigError(f"Failed to update config file with missing keys: {e}")

    return merged_config
