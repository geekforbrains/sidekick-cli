"""
Simplified Sidekick CLI entry point.
"""

import asyncio
import sys

import typer
from rich.console import Console

from sidekick.agent import process_request
from sidekick.config import load_config
from sidekick.constants import APP_NAME, APP_VERSION
from sidekick.types import SessionState
from sidekick.ui import banner, error, info

app = typer.Typer(help=f"{APP_NAME} - Your agentic CLI developer")
console = Console()


async def repl(session: SessionState):
    """Simple REPL loop."""
    await info(f"Using model {session.current_model}")

    while True:
        try:
            # Simple input prompt
            user_input = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            break

        # Process with agent
        try:
            await process_request(session.current_model, user_input, session)
        except Exception as e:
            await error(f"Error: {str(e)}")

    await info("Thanks for all the fish.")


@app.command()
def main(version: bool = typer.Option(False, "--version", "-v", help="Show version and exit.")):
    """Sidekick CLI main entry point."""
    if version:
        console.print(f"{APP_NAME} version {APP_VERSION}")
        return

    # Show banner
    asyncio.run(banner())

    # Load config
    try:
        config = load_config()
        session = SessionState(user_config=config, current_model=config["default_model"])
    except Exception as e:
        asyncio.run(error(f"Failed to load config: {str(e)}"))
        sys.exit(1)

    # Start REPL
    try:
        asyncio.run(repl(session))
    except Exception as e:
        asyncio.run(error(f"Fatal error: {str(e)}"))
        sys.exit(1)


if __name__ == "__main__":
    app()
