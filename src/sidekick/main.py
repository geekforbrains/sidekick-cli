import asyncio

import typer
from rich.console import Console

from sidekick import ui
from sidekick.agent import get_or_create_agent, process_request
from sidekick.config import load_config
from sidekick.constants import APP_NAME, APP_VERSION
from sidekick.session import SessionState

app = typer.Typer(help=f"{APP_NAME} - Your agentic CLI developer")
console = Console()


async def repl(session: SessionState):
    await ui.info(f"Using model {session.current_model}")
    agent = get_or_create_agent(session.current_model, session)

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

            resp = await process_request(session.current_model, user_input, session)
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
    session = SessionState(user_config=config, current_model=config["default_model"])
    asyncio.run(repl(session))


if __name__ == "__main__":
    app()
