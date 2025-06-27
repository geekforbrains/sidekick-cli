"""MCP server utilities and configurations."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from mcp.client.stdio import StdioServerParameters, stdio_client
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.tools import RunContext

from sidekick import ui
from sidekick.config import (ConfigError, parse_mcp_servers, read_config_file,
                             validate_config_structure)
from sidekick.ui import format_server_name

logger = logging.getLogger(__name__)


async def mcp_tool_confirmation_callback(
    ctx: RunContext[Any],
    original_call_tool,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Any:
    """Process tool callback that shows confirmation for ALL MCP tool calls.

    This callback is invoked for every MCP tool call and ensures that
    confirmations are shown regardless of yolo mode or other settings.
    """
    from sidekick.session import session

    # Check if we have the confirmation callback available
    if hasattr(ctx.deps, "confirm_action") and ctx.deps.confirm_action:
        if session.spinner:
            session.spinner.stop()

        # Format the arguments for display
        from rich.pretty import Pretty

        args_display = Pretty(arguments, expand_all=True)

        # Always show confirmation for MCP tools
        confirmed = await ctx.deps.confirm_action(f"MCP({tool_name})", args_display, None)

        if not confirmed:
            raise asyncio.CancelledError("MCP tool execution cancelled by user")

        if session.spinner:
            session.spinner.start()

    # Call the original tool
    return await original_call_tool(tool_name, arguments)


class SilentMCPServerStdio(MCPServerStdio):
    """MCPServerStdio that suppresses stderr output.

    Extends pydantic_ai's MCPServerStdio to redirect stderr to /dev/null,
    preventing MCP server error messages from cluttering the CLI output.
    """

    def __init__(self, *args, display_name: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        # Add display_name for better server identification in logs/UI
        self.display_name = display_name or self.command

    @asynccontextmanager
    async def client_streams(self):
        """Override parent's client_streams to suppress stderr.

        The parent implementation logs errors to stderr by default.
        This override redirects stderr to /dev/null to keep the CLI clean.
        """
        server = StdioServerParameters(
            command=self.command, args=list(self.args), env=self.env, cwd=self.cwd
        )
        # Key change: errlog=null_stream instead of default stderr
        with open(os.devnull, "w") as null_stream:
            async with stdio_client(server=server, errlog=null_stream) as (
                read_stream,
                write_stream,
            ):
                yield read_stream, write_stream


def create_mcp_server(key: str, config: Dict[str, Any]) -> SilentMCPServerStdio:
    """Create a single MCP server instance.

    Args:
        key: Server identifier
        config: Server configuration dictionary

    Returns:
        SilentMCPServerStdio: Configured server instance
    """
    # Use 'name' field if present, otherwise format the key
    display_name = config.get("name", format_server_name(key))

    return SilentMCPServerStdio(
        command=config["command"],
        args=config["args"],
        env=config.get("env", {}),
        display_name=display_name,
        process_tool_call=mcp_tool_confirmation_callback,
    )


def load_mcp_servers() -> List[SilentMCPServerStdio]:
    """Load MCP servers from configuration.

    Returns:
        List of configured MCP server instances

    Note:
        - Returns empty list if no servers configured
        - Shows warnings for invalid server configs but continues with valid ones
    """
    try:
        config = read_config_file()
        validate_config_structure(config)
        mcp_servers_config = parse_mcp_servers(config)
    except ConfigError as e:
        logger.error(f"Failed to load config: {e}", exc_info=True)
        ui.error(f"Failed to load MCP configuration: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}", exc_info=True)
        ui.error(f"Unexpected error loading MCP configuration: {e}")
        return []

    servers = []
    failed_servers = []

    for key, server_config in mcp_servers_config.items():
        try:
            server = create_mcp_server(key, server_config)
            servers.append(server)
        except Exception as e:
            logger.warning(f"Failed to create server '{key}': {e}", exc_info=True)
            display_name = server_config.get("name", format_server_name(key))
            failed_servers.append((display_name, str(e)))

    # Show errors for failed servers
    if failed_servers:
        ui.warning("Some MCP servers failed to load:")
        for server_name, error in failed_servers:
            ui.bullet(f"{server_name}: {error}")

    # Show summary if all servers failed
    if mcp_servers_config and not servers:
        ui.error("No MCP servers could be loaded successfully")
    elif servers and failed_servers:
        ui.info(f"Loaded {len(servers)} of {len(mcp_servers_config)} MCP servers")

    return servers
