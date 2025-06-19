"""Agent wrapper that manages MCP server lifecycle."""
from pydantic_ai import Agent


class ResilientAgent:
    """Manages MCP server lifecycle for an agent."""
    
    def __init__(self, agent: Agent):
        self._agent = agent
        self._mcp_context = None
        self._mcp_entered = False
    
    @property
    def agent(self) -> Agent:
        return self._agent
    
    async def __aenter__(self):
        if not self._mcp_entered:
            self._mcp_context = self._agent.run_mcp_servers()
            await self._mcp_context.__aenter__()
            self._mcp_entered = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._mcp_context and self._mcp_entered:
            await self._mcp_context.__aexit__(exc_type, exc_val, exc_tb)
            self._mcp_entered = False
            self._mcp_context = None