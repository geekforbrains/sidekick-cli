import asyncio
import logging
import signal
import sys

import typer
from rich.console import Console

from sidekick import ui
from sidekick.agent import get_or_create_agent, process_request
from sidekick.commands import handle_command
from sidekick.config import (
    ConfigError,
    ConfigValidationError,
    config_exists,
    ensure_config_structure,
    set_env_vars,
    validate_config_structure,
)
from sidekick.constants import APP_NAME, APP_VERSION
from sidekick.mcp import load_mcp_servers
from sidekick.session import session
from sidekick.setup import run_setup
from sidekick.utils.error import ErrorContext
from sidekick.utils.guide import load_guide
from sidekick.utils.input import create_multiline_prompt_session, get_multiline_input
from sidekick.utils.logger import setup_logging

app = typer.Typer(help=f"{APP_NAME} - Your agentic CLI developer")
console = Console()
log = logging.getLogger(__name__)


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
    servers = load_mcp_servers()
    ui.info("Starting MCP servers")
    if servers:
        for server in servers:
            ui.bullet(server.display_name)
    else:
        ui.bullet("No servers configured")


async def handle_user_request(user_input: str, mcp_agent):
    """Process a user request with proper exception handling."""
    log.debug(f"Handling user request: {user_input.replace('\n', ' ')[:100]}...")
    ui.start_spinner(ui.get_thinking_message())
    session.sigint_received = False

    request_task = asyncio.create_task(process_request(user_input))
    session.current_task = request_task

    async def recreate_agent():
        nonlocal mcp_agent
        if session.current_model in session.agents:
            if mcp_agent._mcp_entered:
                await mcp_agent.__aexit__(None, None, None)
            del session.agents[session.current_model]
            mcp_agent = get_or_create_agent()
            await mcp_agent.__aenter__()

    ctx = ErrorContext("request", ui)

    try:
        resp = await request_task
        ui.stop_spinner()
        if resp:
            has_footer = bool(session.last_usage)
            ui.agent(resp, has_footer=has_footer)
            if session.last_usage:
                ui.usage(session.last_usage)
    except asyncio.CancelledError as e:
        ctx.add_cleanup(recreate_agent)
        await ctx.handle(e)
    except KeyboardInterrupt:
        ui.stop_spinner()
        if not request_task.done():
            request_task.cancel()
            try:
                await request_task
            except asyncio.CancelledError:
                pass
        ui.warning("Request interrupted")
    except Exception as e:
        await ctx.handle(e)
    finally:
        session.current_task = None

    return mcp_agent


async def handle_model_switch(mcp_agent):
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
        return mcp_agent


async def repl():
    ui.info(f"Using model {session.current_model}")
    mcp_agent = get_or_create_agent()

    await display_server_info()

    loop = asyncio.get_event_loop()
    session.sigint_received = False
    signal_handler = setup_signal_handler(loop)

    ui.start_spinner("Initializing servers...", ui.SpinnerStyle.MUTED)
    async with mcp_agent:
        ui.stop_spinner()
        ui.success("Go kick some ass!")
        prompt_session = create_multiline_prompt_session()

        while True:
            ui.line()

            try:
                user_input = await get_multiline_input(prompt_session)
            except (EOFError, KeyboardInterrupt):
                break

            ui.line()

            # Reset context after user input
            # This is for consistent UI styling/spacing
            ui.reset_output_context()

            if not user_input:
                continue

            if should_exit(user_input):
                break

            if await handle_command(user_input):
                if session.model_switched:
                    mcp_agent = await handle_model_switch(mcp_agent)
                continue

            mcp_agent = await handle_user_request(user_input, mcp_agent)
            signal.signal(signal.SIGINT, signal_handler)

    restore_default_signal_handler()
    ui.info("Thanks for all the fish.")


def setup_and_run_event_loop(coro):
    """Create and run event loop with proper cleanup."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging to file."),
):
    """Sidekick CLI main entry point."""
    if version:
        console.print(f"{APP_NAME} version {APP_VERSION}")
        return

    if debug:
        session.debug_enabled = True

    setup_logging(debug_enabled=debug)

    ui.banner()

    if not config_exists():
        console.print()
        config = run_setup()
        set_env_vars(config.get("env", {}))
    else:
        try:
            config = ensure_config_structure()
            validate_config_structure(config)
            set_env_vars(config.get("env", {}))
        except ConfigError as e:
            ui.error("Configuration error", str(e))
            sys.exit(1)
        except ConfigValidationError as e:
            ui.error("Invalid configuration", str(e))
            sys.exit(1)
        except Exception as e:
            ui.error("Failed to load configuration", str(e))
            sys.exit(1)

    session.init(config, config["default_model"])

    if load_guide(session):
        ui.info("Loaded SIDEKICK.md guide")

    log.debug(f"Session initialized with model: {session.current_model}")

    # Create event loop manually to avoid asyncio.run's signal handling
    setup_and_run_event_loop(repl())


if __name__ == "__main__":
    app()
