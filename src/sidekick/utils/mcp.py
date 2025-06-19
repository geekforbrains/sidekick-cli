"""MCP server utilities and configurations."""
import os
from contextlib import asynccontextmanager

from pydantic_ai.mcp import MCPServerStdio
from mcp.client.stdio import StdioServerParameters, stdio_client


class SilentMCPServerStdio(MCPServerStdio):
    """MCPServerStdio that suppresses stderr output."""
    
    @asynccontextmanager
    async def client_streams(self):
        server = StdioServerParameters(
            command=self.command,
            args=list(self.args),
            env=self.env,
            cwd=self.cwd
        )
        # Open /dev/null for writing stderr
        with open(os.devnull, 'w') as null_stream:
            async with stdio_client(server=server, errlog=null_stream) as (read_stream, write_stream):
                yield read_stream, write_stream


def fetch_server():
    """Create a silent MCP fetch server."""
    return SilentMCPServerStdio(
        "uvx",
        args=["mcp-server-fetch"],
    )


def brave_search_server():
    """Create a silent MCP Brave search server."""
    return SilentMCPServerStdio(
        "npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env={"BRAVE_API_KEY": "BSANgzuH-zsMsCsZ371rHjhBkYaQm5j"},
    )