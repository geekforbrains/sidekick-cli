"""MCP server utilities and configurations."""
import os
from contextlib import asynccontextmanager

from pydantic_ai.mcp import MCPServerStdio
from mcp.client.stdio import StdioServerParameters, stdio_client


class SilentMCPServerStdio(MCPServerStdio):
    """MCPServerStdio that suppresses stderr output."""
    
    def __init__(self, *args, display_name: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_name = display_name or self.command
    
    @asynccontextmanager
    async def client_streams(self):
        server = StdioServerParameters(
            command=self.command,
            args=list(self.args),
            env=self.env,
            cwd=self.cwd
        )
        print(f"[LIFECYCLE] Creating stdio client for {self.display_name}")
        with open(os.devnull, 'w') as null_stream:
            async with stdio_client(server=server, errlog=null_stream) as (read_stream, write_stream):
                print(f"[LIFECYCLE] {self.display_name} client streams established")
                yield read_stream, write_stream
                print(f"[LIFECYCLE] {self.display_name} client streams closing")


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