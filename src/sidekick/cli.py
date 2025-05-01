import asyncio

import typer

from sidekick import config, session, ui, events
from sidekick.repl import repl
from sidekick.setup import setup
from sidekick.utils.system import check_for_updates

app = typer.Typer(help=config.NAME)


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
        typer.echo(config.VERSION)
        return

    ui.subscribe_to_events()
    ui.show_banner()
    events.success("Testing")

    has_update, latest_version = check_for_updates()
    if has_update:
        ui.show_update_message(latest_version)

    if no_telemetry:
        session.telemetry_enabled = False

    try:
        asyncio.run(setup(run_setup))
        asyncio.run(repl())
    except Exception as e:
        ui.error(str(e))


if __name__ == "__main__":
    app()
