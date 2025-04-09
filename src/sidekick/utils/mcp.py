"""
MCP (Model Context Protocol) integration utilities for Sidekick.
"""

import io
import os
import subprocess
import sys
from contextlib import contextmanager
from pydantic_ai.mcp import MCPServerStdio
from . import ui


@contextmanager
def suppress_stdout():
    """
    Context manager to temporarily redirect stdout to suppress output.
    """
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = original_stdout


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
        # Extract command and arguments
        command = server_config.get("command")
        args = server_config.get("args", [])

        if not command:
            continue

        # Handle environment variables if specified
        env_vars = server_config.get("env", {})

        # Initialize server using stdio transport
        # Note: Currently only stdio is supported
        with suppress_stdout():
            server = MCPServerStdio(command=command, args=args, env=env_vars)

        mcp_servers.append(server)

    return mcp_servers
