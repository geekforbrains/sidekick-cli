"""
MCP (Model Context Protocol) integration utilities for Sidekick.
"""

import os
from contextlib import AsyncExitStack, contextmanager

from pydantic_ai.mcp import MCPServerStdio

from sidekick import session

from . import ui


@contextmanager
def suppress_subprocess_output():
    """
    Context manager to suppress output from subprocesses by redirecting
    the actual file descriptors for stdout and stderr to /dev/null.
    This captures output even from child processes that write directly to fd 1 and 2.
    """
    # Create temporary files for the original stdout and stderr
    saved_stdout_fd = None
    saved_stderr_fd = None
    null_fd = None

    try:
        # Save the original file descriptors
        saved_stdout_fd = os.dup(1)  # stdout
        saved_stderr_fd = os.dup(2)  # stderr

        # Open /dev/null for writing
        null_fd = os.open(os.devnull, os.O_WRONLY)

        # Redirect stdout and stderr to /dev/null
        os.dup2(null_fd, 1)  # Redirect stdout
        os.dup2(null_fd, 2)  # Redirect stderr

        yield
    finally:
        # Restore original file descriptors
        if saved_stdout_fd is not None:
            os.dup2(saved_stdout_fd, 1)
            os.close(saved_stdout_fd)
        if saved_stderr_fd is not None:
            os.dup2(saved_stderr_fd, 2)
            os.close(saved_stderr_fd)
        if null_fd is not None:
            os.close(null_fd)


def init_mcp_servers(config=None):
    """
    Initialize MCP servers from the user configuration.

    Args:
        config: Dictionary of MCP server configurations from user config

    Returns:
        List of initialized MCP server objects
    """
    if not config:
        return []

    mcp_servers = []

    for server_name, server_config in config.items():
        ui.status(f"Initializing MCP server: {server_name}")
        command = server_config.get("command")
        args = server_config.get("args", [])

        if not command:
            continue

        env_vars = server_config.get("env", {})

        # Initialize server using stdio transport
        # Note: Currently only stdio is supported
        # TODO: Add support for other transports (e.g., HTTP)
        server = MCPServerStdio(command=command, args=args, env=env_vars)
        mcp_servers.append(server)

    return mcp_servers


async def start_mcp_servers():
    """
    Start all MCP servers at application startup.
    """
    if session.mcp_servers_running:
        return

    if not session.mcp_servers:
        ui.status("No MCP servers configured.")
        return

    session.mcp_exit_stack = AsyncExitStack()

    for server in session.mcp_servers:
        with suppress_subprocess_output():
            await session.mcp_exit_stack.enter_async_context(server)

    session.mcp_servers_running = True


async def stop_mcp_servers():
    """
    Stop all running MCP servers.
    """
    if not session.mcp_servers_running or not session.mcp_exit_stack:
        return

    ui.status("Stopping MCP servers...")

    # Suppress output during server shutdown by redirecting file descriptors
    with suppress_subprocess_output():
        await session.mcp_exit_stack.aclose()

    session.mcp_exit_stack = None
    session.mcp_servers_running = False
    ui.status("All MCP servers stopped")
