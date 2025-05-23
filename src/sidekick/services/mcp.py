import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator, List, Optional, Tuple

from pydantic_ai.mcp import MCPServerStdio

from sidekick.exceptions import MCPError
from sidekick.types import MCPServers

if TYPE_CHECKING:
    from mcp.client.stdio import ReadStream, WriteStream

    from sidekick.core.state import StateManager


class QuietMCPServer(MCPServerStdio):
    """A version of ``MCPServerStdio`` that suppresses *all* output coming from the
    MCP server's **stderr** stream.

    We can't just redirect the server's *stdout* because that is where the JSON‑RPC
    protocol messages are sent.  Instead we override ``client_streams`` so we can
    hand our own ``errlog`` (``os.devnull``) to ``mcp.client.stdio.stdio_client``.
    """

    @asynccontextmanager
    async def client_streams(self) -> AsyncIterator[Tuple["ReadStream", "WriteStream"]]:
        """Start the subprocess exactly like the parent class but silence *stderr*."""
        # Local import to avoid cycles
        from mcp.client.stdio import StdioServerParameters, stdio_client

        server_params = StdioServerParameters(
            command=self.command,
            args=list(self.args),
            env=self.env or os.environ,
        )

        # Open ``/dev/null`` for the lifetime of the subprocess so anything the
        # server writes to *stderr* is discarded.
        #
        # This is to help with noisy MCP's that have options for verbosity
        encoding: Optional[str] = getattr(server_params, "encoding", None)
        with open(os.devnull, "w", encoding=encoding) as devnull:
            async with stdio_client(server=server_params, errlog=devnull) as (
                read_stream,
                write_stream,
            ):
                yield read_stream, write_stream


def get_mcp_servers(state_manager: "StateManager") -> List[MCPServerStdio]:
    """Load MCP servers from configuration.

    Args:
        state_manager: The state manager containing user configuration

    Returns:
        List of MCP server instances

    Raises:
        MCPError: If a server configuration is invalid
    """
    mcp_servers: MCPServers = state_manager.session.user_config.get("mcpServers", {})
    loaded_servers: List[MCPServerStdio] = []
    MCPServerStdio.log_level = "critical"

    for server_name, conf in mcp_servers.items():
        try:
            # loaded_servers.append(QuietMCPServer(**conf))
            mcp_instance = MCPServerStdio(**conf)
            # mcp_instance.log_level = "critical"
            loaded_servers.append(mcp_instance)
        except Exception as e:
            raise MCPError(
                server_name=server_name,
                message=f"Failed to create MCP server: {str(e)}",
                original_error=e,
            )

    return loaded_servers
