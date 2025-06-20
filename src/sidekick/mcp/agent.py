"""Agent wrapper that manages MCP server lifecycle.

This module provides a wrapper around pydantic_ai.Agent that ensures MCP (Model Context Protocol)
servers are properly started and stopped when using the agent.
"""

from pydantic_ai import Agent


class MCPAgent:
    """Manages MCP server lifecycle for an agent.

    This is a context manager wrapper that ensures MCP servers are running when needed
    and properly cleaned up afterwards. It wraps a pydantic_ai.Agent instance and manages
    the lifecycle of its MCP servers without modifying the agent's behavior.

    The wrapper is reusable - it can be entered and exited multiple times, starting and
    stopping MCP servers as needed. This is useful for long-running applications where
    the agent is created once but used for multiple requests (ie. REPL).

    Key design points:
    - Does NOT inherit from Agent - uses composition instead of inheritance
    - Provides transparent access to the wrapped agent via the .agent property
    - Tracks state to prevent double-starting or stopping of MCP servers
    - Handles async context manager protocol for proper resource management
    """

    def __init__(self, agent: Agent):
        """Initialize the MCP agent wrapper.

        Args:
            agent: A pydantic_ai.Agent instance that may have MCP servers configured.
                   The agent should already have its model, tools, and MCP servers set up.
        """
        self._agent = agent
        self._mcp_context = None  # Stores the context manager from agent.run_mcp_servers()
        self._mcp_entered = False  # Tracks whether we've entered the MCP context

    @property
    def agent(self) -> Agent:
        """Access the wrapped pydantic_ai.Agent instance.

        This property allows direct access to the underlying agent for running conversations,
        accessing tools, or any other agent operations. The wrapper does not intercept or
        modify any agent methods - it only manages the MCP server lifecycle.

        Returns:
            The wrapped pydantic_ai.Agent instance
        """
        return self._agent

    async def __aenter__(self):
        """Enter the async context and start MCP servers.

        This method starts all MCP servers configured on the agent by calling
        agent.run_mcp_servers(). The method is idempotent - if called multiple times
        without exiting, it will only start the servers once.

        The actual server startup is delegated to pydantic_ai's implementation which:
        1. Iterates through all MCPServerStdio instances in agent._mcp_servers
        2. Starts each server process and establishes stdio communication
        3. Returns a context manager that handles shutdown

        Returns:
            self: Returns this MCPAgent instance for use in async with statements
        """
        if not self._mcp_entered:
            # Get the context manager from pydantic_ai that manages MCP servers
            self._mcp_context = self._agent.run_mcp_servers()
            # Enter the context to actually start the servers
            await self._mcp_context.__aenter__()
            self._mcp_entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context and stop MCP servers.

        This method ensures all MCP servers are properly shut down by delegating to
        the pydantic_ai context manager. It resets the internal state so the wrapper
        can be reused.

        The cleanup process includes:
        1. Sending shutdown signals to all MCP server processes
        2. Waiting for processes to terminate gracefully
        3. Cleaning up any stdio connections

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self._mcp_context and self._mcp_entered:
            # Delegate cleanup to pydantic_ai's context manager
            await self._mcp_context.__aexit__(exc_type, exc_val, exc_tb)
            self._mcp_entered = False
            self._mcp_context = None
