import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from pydantic_ai.mcp import MCPServerStdio

if TYPE_CHECKING:
    from sidekick.core.state import StateManager


class QuietMCPServer(MCPServerStdio):
    """A version of ``MCPServerStdio`` that suppresses *all* output coming from the
    MCP server's **stderr** stream.

    We can't just redirect the server's *stdout* because that is where the JSON‑RPC
    protocol messages are sent.  Instead we override ``client_streams`` so we can
    hand our own ``errlog`` (``os.devnull``) to ``mcp.client.stdio.stdio_client``.
    """

    @asynccontextmanager
    async def client_streams(self):  # type: ignore[override]
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
        with open(os.devnull, "w", encoding=server_params.encoding) as devnull:
            async with stdio_client(server=server_params, errlog=devnull) as (
                read_stream,
                write_stream,
            ):
                yield read_stream, write_stream


def get_mcp_servers(state_manager: "StateManager"):
    mcp_servers = state_manager.session.user_config.get("mcpServers", {})
    loaded_servers = []
    MCPServerStdio.log_level = "critical"

    for conf in mcp_servers.values():
        # loaded_servers.append(QuietMCPServer(**conf))
        mcp_instance = MCPServerStdio(**conf)
        # mcp_instance.log_level = "critical"
        loaded_servers.append(mcp_instance)

    return loaded_servers
