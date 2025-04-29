import asyncio

import typer

from sidekick import config, session, ui
from sidekick.setup import setup
from sidekick.repl import repl
from sidekick.utils.system import check_for_updates

app = typer.Typer(help=config.NAME)


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
    logfire_enabled: bool = typer.Option(False, "--logfire", help="Enable Logfire tracing."),
    no_telemetry: bool = typer.Option(
        False, "--no-telemetry", help="Disable telemetry collection."
    ),
):
    if version:
        typer.echo(config.VERSION)
        return

    ui.show_banner()

    has_update, latest_version = check_for_updates()
    if has_update:
        ui.show_update_message(latest_version)

    if no_telemetry:
        session.telemetry_enabled = False

    asyncio.run(setup())
    # asyncio.run(repl())


if __name__ == "__main__":
    app()
