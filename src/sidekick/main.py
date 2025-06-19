import asyncio
import signal

import typer
from rich.console import Console

from sidekick import session, ui
from sidekick.agent import get_or_create_agent, process_request
from sidekick.config import load_config
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


async def handle_command(user_input: str) -> bool:
    """Handle slash commands. Returns True if command was handled."""
    if not user_input.startswith("/"):
        return False

    if user_input == "/dump":
        await ui.dump(session.messages)
    elif user_input == "/yolo":
        # Toggle confirmations on/off
        session.confirmation_enabled = not session.confirmation_enabled
        status = "disabled (YOLO mode)" if not session.confirmation_enabled else "enabled"
        await ui.info(f"Tool confirmations {status}")

    return True


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
    ui.start_spinner("Thinking...")
    session.sigint_received = False

    request_task = asyncio.create_task(process_request(user_input))
    session.current_task = request_task

    try:
        resp = await request_task
        ui.stop_spinner()
        if resp:
            await ui.agent(resp)
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
        await ui.error(f"Error processing request: {e}")
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

    # Load config or run setup if needed
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        if (
            "Config file not found" in str(e)
            or "Config missing" in str(e)
            or "Invalid JSON" in str(e)
        ):
            console.print()
            config = run_setup()

            # Set environment variables from the new config
            for key, value in config.get("env", {}).items():
                if value:
                    import os

                    os.environ[key] = value
        else:
            raise

    session.init(config, config["default_model"])

    # Create event loop manually to avoid asyncio.run's signal handling
    setup_and_run_event_loop(repl())


if __name__ == "__main__":
    app()
