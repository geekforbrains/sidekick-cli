import asyncio
import signal

import typer
from rich.console import Console

from sidekick import session, ui
from sidekick.agent import get_or_create_agent, process_request
from sidekick.config import load_config
from sidekick.constants import APP_NAME, APP_VERSION
from sidekick.utils.mcp import get_configured_servers

app = typer.Typer(help=f"{APP_NAME} - Your agentic CLI developer")
console = Console()


async def repl():
    await ui.info(f"Using model {session.current_model}")
    print("[LIFECYCLE] Creating initial agent")
    resilient_agent = get_or_create_agent()

    servers = get_configured_servers()
    await ui.info("Starting MCP servers")
    if servers:
        for server in servers:
            await ui.bullet(server.display_name)
    else:
        await ui.bullet("No servers configured")
    
    spinner = console.status("[dim]Initializing servers...[/dim]", spinner="dots")
    spinner.start()
    
    # Store the event loop for signal handler
    loop = asyncio.get_event_loop()
    
    # Track if we received a SIGINT for the current request
    session.sigint_received = False
    
    # Set up signal handler for Ctrl+C
    def signal_handler(signum, frame):
        print(f"\n[DEBUG] Signal handler called, current_task: {session.current_task}, done: {session.current_task.done() if session.current_task else 'N/A'}")
        session.sigint_received = True
        if session.current_task and not session.current_task.done():
            # Schedule the cancellation in the event loop
            print("[DEBUG] Cancelling current task")
            loop.call_soon_threadsafe(session.current_task.cancel)
        else:
            # If no task is running, raise KeyboardInterrupt to exit
            print("[DEBUG] No active task, raising KeyboardInterrupt")
            raise KeyboardInterrupt()
    
    # Install our signal handler
    signal.signal(signal.SIGINT, signal_handler)
    print(f"[DEBUG] Installed custom signal handler")
    
    # Enter the resilient agent context (which manages MCP servers)
    print("[LIFECYCLE] Entering main REPL context")
    async with resilient_agent:
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
            
            # Reset sigint flag for new request
            session.sigint_received = False
            print(f"[DEBUG] Starting new request, sigint_received reset to {session.sigint_received}")
            
            # Create task for request processing
            print(f"[DEBUG] Creating task for: {user_input}")
                
            request_task = asyncio.create_task(process_request(user_input))
            session.current_task = request_task
            print(f"[DEBUG] Task created: {request_task}")
            
            try:
                print("[DEBUG] Awaiting task...")
                resp = await request_task
                print(f"[DEBUG] Task completed normally with response: {resp[:50] if resp else None}...")
                if resp:
                    await ui.agent(resp)
            except asyncio.CancelledError:
                print("[DEBUG] Task was cancelled")
                await ui.warning("Request cancelled")
                # Clear the agent from cache to force recreation with fresh MCP connections
                if session.current_model in session.agents:
                    print(f"[LIFECYCLE] Clearing agent cache for model: {session.current_model}")
                    # First exit the resilient agent context if it's active
                    if resilient_agent._mcp_entered:
                        print("[LIFECYCLE] Exiting current agent context")
                        await resilient_agent.__aexit__(None, None, None)
                    del session.agents[session.current_model]
                    # Get a fresh agent for next request
                    print("[LIFECYCLE] Creating new agent after cancellation")
                    resilient_agent = get_or_create_agent()
                    # Re-enter the context
                    print("[LIFECYCLE] Re-entering agent context")
                    await resilient_agent.__aenter__()
            except KeyboardInterrupt:
                print("[DEBUG] KeyboardInterrupt during task")
                # Cancel the task if it's still running
                if not request_task.done():
                    request_task.cancel()
                    try:
                        await request_task
                    except asyncio.CancelledError:
                        pass
                await ui.warning("Request interrupted")
            except Exception as e:
                print(f"[DEBUG] Exception during task: {type(e).__name__}: {e}")
                await ui.error(f"Error processing request: {e}")
            finally:
                # Always clean up spinner and task
                print("[DEBUG] Cleaning up...")
                if session.spinner:
                    session.spinner.stop()
                    session.spinner = None
                session.current_task = None
                print(f"[DEBUG] Cleanup done, current_task: {session.current_task}")
                
                # Re-install our custom handler (in case it was changed)
                signal.signal(signal.SIGINT, signal_handler)

    # Restore default signal handler
    print(f"[DEBUG] Restoring default signal handler")
    signal.signal(signal.SIGINT, signal.default_int_handler)
    
    print("[LIFECYCLE] REPL shutdown complete")
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
