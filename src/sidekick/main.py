import asyncio
import logging
import sys

import typer
from rich.console import Console

from sidekick import ui
from sidekick.config import (
    ConfigError,
    ConfigValidationError,
    config_exists,
    ensure_config_structure,
    set_env_vars,
    validate_config_structure,
)
from sidekick.constants import APP_NAME, APP_VERSION
from sidekick.repl import Repl
from sidekick.session import session
from sidekick.setup import run_setup
from sidekick.utils.guide import load_guide
from sidekick.utils.logger import setup_logging

app = typer.Typer(help=f"{APP_NAME} - Your agentic CLI developer")
console = Console()
log = logging.getLogger(__name__)


def _setup_and_run_event_loop(coro):
    """
    Create, run, and properly clean up the asyncio event loop.

    This manual setup is used instead of the simpler `asyncio.run()` to gain
    direct access to the loop object. This is necessary because OS signal
    handlers (like for SIGINT/Ctrl+C) execute outside of the asyncio loop's
    context. To gracefully cancel a task from the handler, we must use
    `loop.call_soon_threadsafe()` to safely schedule the cancellation
    within the running loop.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


def _initialize_config():
    """Checks for, loads, and validates the application configuration."""
    ui.banner()

    if not config_exists():
        console.print()
        config = run_setup()
    else:
        try:
            config = ensure_config_structure()
            validate_config_structure(config)
        except ConfigError as e:
            ui.error("Configuration error", str(e))
            sys.exit(1)
        except ConfigValidationError as e:
            ui.error("Invalid configuration", str(e))
            sys.exit(1)
        except Exception as e:
            ui.error("Failed to load configuration", str(e))
            sys.exit(1)

    set_env_vars(config.get("env", {}))
    return config


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

    config = _initialize_config()
    session.init(config, config["default_model"])

    project_guide = load_guide()
    if project_guide:
        ui.info("Loaded SIDEKICK.md guide")

    log.debug(f"Session initialized with model: {session.current_model}")

    repl = Repl(project_guide=project_guide)
    _setup_and_run_event_loop(repl.run())


if __name__ == "__main__":
    app()
