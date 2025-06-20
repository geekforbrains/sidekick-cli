import asyncio
import json
import signal
import sys
import traceback

import typer
from rich.console import Console

from sidekick import session, ui
from sidekick.agent import get_or_create_agent, process_request
from sidekick.commands import handle_command
from sidekick.config import (ConfigValidationError, config_exists, read_config_file, set_env_vars,
                             validate_config_structure)
from sidekick.constants import APP_NAME, APP_VERSION
from sidekick.mcp import get_configured_servers
from sidekick.setup import run_setup

app = typer.Typer(help=f"{APP_NAME} - Your agentic CLI developer")
console = Console()


def setup_signal_handler(loop):
    """Set up SIGINT handler for graceful cancellation."""

    def signal_handler(signum, frame):
        session.sigint_received = True
        if session.current_task and not session.current_task.done():
            loop.call_soon_threadsafe(session.current_task.cancel)
        else:
            raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)
    return signal_handler


def restore_default_signal_handler():
    """Restore the default SIGINT handler."""
    signal.signal(signal.SIGINT, signal.default_int_handler)


def should_exit(user_input: str) -> bool:
    """Check if user wants to exit."""
    return user_input.lower() in ["exit", "quit"]


async def display_server_info():
    """Display information about configured MCP servers."""
    servers = get_configured_servers()
    await ui.info("Starting MCP servers")
    if servers:
        for server in servers:
            await ui.bullet(server.display_name)
    else:
        await ui.bullet("No servers configured")


async def initialize_servers():
    """Initialize MCP servers with spinner feedback."""
    ui.stop_spinner()


async def handle_user_request(user_input: str, mcp_agent):
    """Process a user request with proper exception handling."""
    ui.start_spinner(ui.get_thinking_message())
    session.sigint_received = False

    request_task = asyncio.create_task(process_request(user_input))
    session.current_task = request_task

    try:
        resp = await request_task
        ui.stop_spinner()
        if resp:
            await ui.agent(resp)
            # Display usage information if available
            if session.last_usage:
                await ui.usage(session.last_usage)
        # If resp is None, it means the tool was cancelled by user, which is already handled
    except asyncio.CancelledError:
        ui.stop_spinner()
        await ui.warning("Request cancelled")
        # Recreate agent after cancellation
        if session.current_model in session.agents:
            if mcp_agent._mcp_entered:
                await mcp_agent.__aexit__(None, None, None)
            del session.agents[session.current_model]
            mcp_agent = get_or_create_agent()
            await mcp_agent.__aenter__()
    except KeyboardInterrupt:
        ui.stop_spinner()
        if not request_task.done():
            request_task.cancel()
            try:
                await request_task
            except asyncio.CancelledError:
                pass
        await ui.warning("Request interrupted")
    except Exception as e:
        ui.stop_spinner()
        tb = traceback.format_exc()
        await ui.error(f"Error processing request: {e}", detail=tb)
    finally:
        ui.stop_spinner()
        session.current_task = None

    return mcp_agent


async def repl():
    await ui.info(f"Using model {session.current_model}")
    mcp_agent = get_or_create_agent()

    await display_server_info()

    loop = asyncio.get_event_loop()
    session.sigint_received = False
    signal_handler = setup_signal_handler(loop)

    ui.start_spinner("Initializing servers...", ui.SpinnerStyle.MUTED)
    async with mcp_agent:
        await initialize_servers()

        await ui.success("Go kick some ass!")
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue

            if should_exit(user_input):
                break

            if await handle_command(user_input):
                # Check if model was switched and recreate agent if needed
                if session.model_switched:
                    ui.start_spinner("Switching model...", ui.SpinnerStyle.MUTED)
                    try:
                        # Exit current agent context
                        if mcp_agent._mcp_entered:
                            await mcp_agent.__aexit__(None, None, None)
                        # Create and enter new agent context
                        mcp_agent = get_or_create_agent()
                        await mcp_agent.__aenter__()
                        session.model_switched = False
                    finally:
                        ui.stop_spinner()
                continue

            mcp_agent = await handle_user_request(user_input, mcp_agent)
            signal.signal(signal.SIGINT, signal_handler)

    restore_default_signal_handler()
    await ui.info("Thanks for all the fish.")


def setup_and_run_event_loop(coro):
    """Create and run event loop with proper cleanup."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


@app.command()
def main(version: bool = typer.Option(False, "--version", "-v", help="Show version and exit.")):
    """Sidekick CLI main entry point."""
    if version:
        console.print(f"{APP_NAME} version {APP_VERSION}")
        return

    # Run banner separately
    asyncio.run(ui.banner())

    # Check if config exists, run setup if needed
    if not config_exists():
        console.print()
        config = run_setup()
        # Apply env vars from newly created config
        set_env_vars(config.get("env", {}))
    else:
        # Config exists, try to load and validate it
        try:
            config = read_config_file()
            validate_config_structure(config)
            set_env_vars(config.get("env", {}))
        except PermissionError as e:
            asyncio.run(ui.error("Cannot access config file", str(e)))
            sys.exit(1)
        except json.JSONDecodeError as e:
            asyncio.run(ui.error("Invalid JSON in config file", str(e)))
            sys.exit(1)
        except ConfigValidationError as e:
            asyncio.run(ui.error("Invalid configuration", str(e)))
            sys.exit(1)
        except Exception as e:
            asyncio.run(ui.error("Failed to load configuration", str(e)))
            sys.exit(1)

    session.init(config, config["default_model"])

    # Create event loop manually to avoid asyncio.run's signal handling
    setup_and_run_event_loop(repl())


if __name__ == "__main__":
    app()
