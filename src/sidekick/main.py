import asyncio

import typer
from rich.console import Console

from sidekick import session, ui
from sidekick.agent import get_or_create_agent, process_request
from sidekick.config import load_config
from sidekick.constants import APP_NAME, APP_VERSION

app = typer.Typer(help=f"{APP_NAME} - Your agentic CLI developer")
console = Console()


async def repl():
    await ui.info(f"Using model {session.current_model}")
    agent = get_or_create_agent()

    await ui.info("Starting MCP servers")
    async with agent.run_mcp_servers():
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

            session.spinner = console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots")
            session.spinner.start()
            resp = await process_request(user_input)
            session.spinner.stop()
            session.spinner = None
            if resp:
                await ui.agent(resp)

    await ui.info("Thanks for all the fish.")


@app.command()
def main(version: bool = typer.Option(False, "--version", "-v", help="Show version and exit.")):
    """Sidekick CLI main entry point."""
    if version:
        console.print(f"{APP_NAME} version {APP_VERSION}")
        return

    asyncio.run(ui.banner())
    config = load_config()
    session.init(config, config["default_model"])
    asyncio.run(repl())


if __name__ == "__main__":
    app()
