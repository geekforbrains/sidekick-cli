"""Simple agent wrapper that manages MCP server lifecycle."""
from pydantic_ai import Agent


class ResilientAgent:
    """Wrapper around pydantic-ai Agent that manages MCP server lifecycle."""
    
    def __init__(self, agent: Agent):
        self._agent = agent
        self._mcp_context = None
        self._mcp_entered = False
        print(f"[LIFECYCLE] ResilientAgent created with {len(self._agent._mcp_servers)} MCP servers")
    
    @property
    def agent(self) -> Agent:
        """Get the underlying agent."""
        return self._agent
    
    async def __aenter__(self):
        """Enter the MCP server context."""
        if not self._mcp_entered:
            print("[LIFECYCLE] Starting MCP servers...")
            self._mcp_context = self._agent.run_mcp_servers()
            await self._mcp_context.__aenter__()
            self._mcp_entered = True
            print("[LIFECYCLE] MCP servers started successfully")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the MCP server context."""
        if self._mcp_context and self._mcp_entered:
            print("[LIFECYCLE] Stopping MCP servers...")
            await self._mcp_context.__aexit__(exc_type, exc_val, exc_tb)
            self._mcp_entered = False
            self._mcp_context = None
            print("[LIFECYCLE] MCP servers stopped")