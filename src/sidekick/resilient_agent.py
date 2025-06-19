"""Resilient agent wrapper that handles MCP server disconnections gracefully."""
import asyncio
from typing import Any, Optional

from pydantic_ai import Agent
from pydantic_ai.exceptions import UserError

from sidekick import session
from sidekick.utils.mcp import SilentMCPServerStdio


class ResilientAgent:
    """Wrapper around pydantic-ai Agent that handles MCP server resets."""
    
    def __init__(self, agent: Agent):
        self._agent = agent
        self._mcp_context = None
        self._mcp_entered = False
    
    @property
    def agent(self) -> Agent:
        """Get the underlying agent."""
        return self._agent
    
    async def __aenter__(self):
        """Enter the MCP server context."""
        if not self._mcp_entered:
            self._mcp_context = self._agent.run_mcp_servers()
            await self._mcp_context.__aenter__()
            self._mcp_entered = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the MCP server context."""
        if self._mcp_context and self._mcp_entered:
            await self._mcp_context.__aexit__(exc_type, exc_val, exc_tb)
            self._mcp_entered = False
            self._mcp_context = None
    
    def mark_servers_for_reset(self):
        """Mark all MCP servers as needing reset."""
        for server in self._agent._mcp_servers:
            if isinstance(server, SilentMCPServerStdio):
                server.mark_for_reset()
    
    async def reset_mcp_servers_if_needed(self):
        """Reset MCP servers that are marked for reset."""
        servers_to_reset = [
            server for server in self._agent._mcp_servers
            if isinstance(server, SilentMCPServerStdio) and server.needs_reset()
        ]
        
        if servers_to_reset:
            print(f"[DEBUG] Found {len(servers_to_reset)} servers needing reset")
            
            # Clear the _needs_reset flag
            for server in servers_to_reset:
                server._needs_reset = False
            
            # Force recreation of the agent by clearing it from cache
            # This will cause a fresh agent with new MCP connections to be created
            if session.current_model in session.agents:
                print(f"[DEBUG] Clearing agent from cache to force MCP reconnection")
                # Exit the current context first
                if self._mcp_entered:
                    await self.__aexit__(None, None, None)
                
                # Remove from cache
                del session.agents[session.current_model]
                
                # This will trigger recreation on next request
                raise RuntimeError("MCP servers need reset - agent will be recreated")
    
    async def run_with_retry(self, message: str, **kwargs):
        """Run the agent with automatic MCP reset on failure."""
        # First, check if any servers need reset
        await self.reset_mcp_servers_if_needed()
        
        try:
            # Try to run normally
            async with self._agent.run(message, **kwargs) as run:
                return await run.get_output()
        except (asyncio.CancelledError, Exception) as e:
            # On any error, mark servers for reset
            self.mark_servers_for_reset()
            raise
    
    async def iter_with_retry(self, message: str, **kwargs):
        """Iterate through agent responses with automatic MCP reset on failure."""
        # First, check if any servers need reset
        try:
            await self.reset_mcp_servers_if_needed()
        except RuntimeError as e:
            if "MCP servers need reset" in str(e):
                # This is expected - the agent will be recreated
                raise
        
        try:
            # Return the agent.iter() context manager
            return self._agent.iter(message, **kwargs)
        except (asyncio.CancelledError, Exception) as e:
            # On any error, mark servers for reset
            self.mark_servers_for_reset()
            raise