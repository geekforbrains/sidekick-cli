"""MCP server utilities and configurations."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from mcp.client.stdio import StdioServerParameters, stdio_client
from pydantic_ai.mcp import MCPServerStdio

from sidekick.config import (ConfigError, parse_mcp_servers, read_config_file,
                             validate_config_structure)

logger = logging.getLogger(__name__)


class SilentMCPServerStdio(MCPServerStdio):
    """MCPServerStdio that suppresses stderr output.

    Extends pydantic_ai's MCPServerStdio to redirect stderr to /dev/null,
    preventing MCP server error messages from cluttering the CLI output.
    """

    def __init__(self, *args, display_name: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        # Add display_name for better server identification in logs/UI
        self.display_name = display_name or self.command

    @asynccontextmanager
    async def client_streams(self):
        """Override parent's client_streams to suppress stderr.

        The parent implementation logs errors to stderr by default.
        This override redirects stderr to /dev/null to keep the CLI clean.
        """
        server = StdioServerParameters(
            command=self.command, args=list(self.args), env=self.env, cwd=self.cwd
        )
        # Key change: errlog=null_stream instead of default stderr
        with open(os.devnull, "w") as null_stream:
            async with stdio_client(server=server, errlog=null_stream) as (
                read_stream,
                write_stream,
            ):
                yield read_stream, write_stream


def _format_display_name(key: str) -> str:
    """Convert a server key to a display name.

    Examples:
        fetch -> Fetch
        brave-search -> Brave Search
        brave_search -> Brave Search
    """
    return key.replace("-", " ").replace("_", " ").title()


def create_mcp_server(key: str, config: Dict[str, Any]) -> SilentMCPServerStdio:
    """Create a single MCP server instance.

    Args:
        key: Server identifier
        config: Server configuration dictionary

    Returns:
        SilentMCPServerStdio: Configured server instance
    """
    # Use 'name' field if present, otherwise format the key
    display_name = config.get("name", _format_display_name(key))

    return SilentMCPServerStdio(
        command=config["command"],
        args=config["args"],
        env=config.get("env", {}),
        display_name=display_name,
    )


def load_mcp_servers() -> List[SilentMCPServerStdio]:
    """Load MCP servers from configuration.

    Returns:
        List of configured MCP server instances

    Note:
        - Returns empty list if no servers configured
        - Logs warnings for invalid server configs but continues with valid ones
    """
    try:
        config = read_config_file()
        validate_config_structure(config)
        mcp_servers_config = parse_mcp_servers(config)
    except ConfigError as e:
        logger.error(f"Failed to load config: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        return []

    servers = []
    for key, server_config in mcp_servers_config.items():
        try:
            server = create_mcp_server(key, server_config)
            servers.append(server)
        except Exception as e:
            logger.warning(f"Failed to create server '{key}': {e}")

    if mcp_servers_config and not servers:
        logger.warning("No valid MCP servers could be loaded")

    return servers


# Backward compatibility
def get_configured_servers():
    """Get list of configured MCP servers from config file.

    Deprecated: Use load_mcp_servers() instead.
    """
    return load_mcp_servers()
