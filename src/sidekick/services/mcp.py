"""
Module: sidekick.services.mcp

Provides Model Context Protocol (MCP) server management functionality.
Handles MCP server initialization, configuration validation, and client connections.
"""

from typing import TYPE_CHECKING, List

from pydantic_ai.mcp import MCPServerStdio

from sidekick.exceptions import MCPError
from sidekick.types import MCPServers

if TYPE_CHECKING:
    from sidekick.types import SessionState


def get_mcp_servers(session: "SessionState") -> List[MCPServerStdio]:
    """Load MCP servers from configuration.

    Args:
        session: The session state containing user configuration

    Returns:
        List of MCP server instances

    Raises:
        MCPError: If a server configuration is invalid
    """
    mcp_servers: MCPServers = session.user_config.get("mcpServers", {})
    loaded_servers: List[MCPServerStdio] = []

    # Suppress verbose MCP server output
    MCPServerStdio.log_level = "critical"

    for server_name, conf in mcp_servers.items():
        try:
            mcp_instance = MCPServerStdio(**conf)
            loaded_servers.append(mcp_instance)
        except Exception as e:
            raise MCPError(
                server_name=server_name,
                message=f"Failed to create MCP server: {str(e)}",
                original_error=e,
            )

    return loaded_servers
