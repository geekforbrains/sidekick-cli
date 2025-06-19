import asyncio
import signal

import typer
from rich.console import Console

from sidekick import session, ui
from sidekick.agent import get_or_create_agent, process_request
from sidekick.config import load_config
from sidekick.constants import APP_NAME, APP_VERSION
from sidekick.mcp import get_configured_servers

app = typer.Typer(help=f"{APP_NAME} - Your agentic CLI developer")
console = Console()


async def repl():
    await ui.info(f"Using model {session.current_model}")
    mcp_agent = get_or_create_agent()

    servers = get_configured_servers()
    await ui.info("Starting MCP servers")
    if servers:
        for server in servers:
            await ui.bullet(server.display_name)
    else:
        await ui.bullet("No servers configured")

    spinner = console.status("[dim]Initializing servers...[/dim]", spinner="dots")
    spinner.start()

    loop = asyncio.get_event_loop()
    session.sigint_received = False

    def signal_handler(signum, frame):
        session.sigint_received = True
        if session.current_task and not session.current_task.done():
            loop.call_soon_threadsafe(session.current_task.cancel)
        else:
            raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)

    async with mcp_agent:
        await asyncio.sleep(0.5)
        spinner.stop()

        await ui.success("Go kick some ass!")
        while True:
            try:
                user_input = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                break

            if user_input.startswith("/"):
                if user_input == "/dump":
                    await ui.dump(session.messages)
                continue

            # Create a cancellable task for request processing
            session.spinner = console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots")
            session.spinner.start()

            session.sigint_received = False

            request_task = asyncio.create_task(process_request(user_input))
            session.current_task = request_task

            try:
                resp = await request_task
                if session.spinner:
                    session.spinner.stop()
                    session.spinner = None
                if resp:
                    await ui.agent(resp)
            except asyncio.CancelledError:
                if session.spinner:
                    session.spinner.stop()
                    session.spinner = None
                await ui.warning("Request cancelled")
                if session.current_model in session.agents:
                    if mcp_agent._mcp_entered:
                        await mcp_agent.__aexit__(None, None, None)
                    del session.agents[session.current_model]
                    mcp_agent = get_or_create_agent()
                    await mcp_agent.__aenter__()
            except KeyboardInterrupt:
                if session.spinner:
                    session.spinner.stop()
                    session.spinner = None
                if not request_task.done():
                    request_task.cancel()
                    try:
                        await request_task
                    except asyncio.CancelledError:
                        pass
                await ui.warning("Request interrupted")
            except Exception as e:
                if session.spinner:
                    session.spinner.stop()
                    session.spinner = None
                await ui.error(f"Error processing request: {e}")
            finally:
                if session.spinner:
                    session.spinner.stop()
                    session.spinner = None
                session.current_task = None
                signal.signal(signal.SIGINT, signal_handler)

    signal.signal(signal.SIGINT, signal.default_int_handler)
    await ui.info("Thanks for all the fish.")


@app.command()
def main(version: bool = typer.Option(False, "--version", "-v", help="Show version and exit.")):
    """Sidekick CLI main entry point."""
    if version:
        console.print(f"{APP_NAME} version {APP_VERSION}")
        return

    # Run banner separately
    asyncio.run(ui.banner())
    config = load_config()
    session.init(config, config["default_model"])

    # Create event loop manually to avoid asyncio.run's signal handling
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(repl())
    finally:
        loop.close()


if __name__ == "__main__":
    app()
