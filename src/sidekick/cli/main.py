"""
Module: sidekick.cli.main

CLI entry point and main command handling for the Sidekick application.
Manages application startup, version checking, and REPL initialization.
"""

import asyncio

import typer

from sidekick.cli.repl import repl
from sidekick.configuration.settings import ApplicationSettings
from sidekick.core.state import StateManager
from sidekick.setup import setup
from sidekick.ui.output import banner, update_available
from sidekick.ui.panels import error
from sidekick.ui.output import version as version_output
from sidekick.utils.system import check_for_updates

app_settings = ApplicationSettings()
app = typer.Typer(help=app_settings.name)
state_manager = StateManager()


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
    logfire_enabled: bool = typer.Option(False, "--logfire", help="Enable Logfire tracing."),
    no_telemetry: bool = typer.Option(
        False, "--no-telemetry", help="Disable telemetry collection."
    ),
    run_setup: bool = typer.Option(False, "--setup", help="Run setup process."),
):
    if version:
        asyncio.run(version_output())
        return

    asyncio.run(banner())

    has_update, latest_version = check_for_updates()
    if has_update:
        asyncio.run(update_available(latest_version))

    if no_telemetry:
        state_manager.session.telemetry_enabled = False

    try:
        asyncio.run(setup(run_setup, state_manager))
        asyncio.run(repl(state_manager))
    except Exception as e:
        asyncio.run(error(str(e)))


if __name__ == "__main__":
    app()
