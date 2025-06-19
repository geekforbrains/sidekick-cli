"""MCP server utilities and configurations."""
import os
from contextlib import asynccontextmanager
from typing import Optional

from pydantic_ai.mcp import MCPServerStdio
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession


class SilentMCPServerStdio(MCPServerStdio):
    """MCPServerStdio that suppresses stderr output and supports reconnection."""
    
    def __init__(self, *args, display_name: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_name = display_name or self.command
        self._needs_reset = False
        self._is_connected = False
    
    @asynccontextmanager
    async def client_streams(self):
        server = StdioServerParameters(
            command=self.command,
            args=list(self.args),
            env=self.env,
            cwd=self.cwd
        )
        with open(os.devnull, 'w') as null_stream:
            async with stdio_client(server=server, errlog=null_stream) as (read_stream, write_stream):
                self._is_connected = True
                try:
                    yield read_stream, write_stream
                finally:
                    self._is_connected = False
    
    def mark_for_reset(self):
        """Mark this server as needing a reset."""
        self._needs_reset = True
        print(f"[DEBUG] Marked {self.display_name} for reset")
    
    def needs_reset(self) -> bool:
        """Check if this server needs to be reset."""
        return self._needs_reset
    
    def clear_reset_flag(self):
        """Clear the reset flag."""
        self._needs_reset = False


def fetch_server():
    """Create a silent MCP fetch server."""
    return SilentMCPServerStdio(
        "uvx",
        args=["mcp-server-fetch"],
        display_name="Fetch",
    )


def brave_search_server():
    """Create a silent MCP Brave search server."""
    return SilentMCPServerStdio(
        "npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env={"BRAVE_API_KEY": "BSANgzuH-zsMsCsZ371rHjhBkYaQm5j"},
        display_name="Brave Search",
    )


def get_configured_servers():
    """Get list of configured MCP servers."""
    return [fetch_server(), brave_search_server()]