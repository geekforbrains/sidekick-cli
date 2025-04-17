import asyncio

import logfire
import typer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession

from sidekick import config, session
from sidekick.agents.main import MainAgent
from sidekick.commands import CommandHandler
from sidekick.utils import telemetry, ui
from sidekick.utils.setup import setup
from sidekick.utils.system import check_for_updates, cleanup_session
from sidekick.utils.undo import commit_for_undo

app = typer.Typer(help=config.NAME)
kb = KeyBindings()
agent = MainAgent()


@kb.add("escape", "enter")
def _newline(event):
    """Insert a newline character."""
    event.current_buffer.insert_text("\n")


@kb.add("enter")
def _submit(event):
    """Submit the current buffer."""
    event.current_buffer.validate_and_handle()


async def process_request(res, compact=False):
    ui.line()
    msg = "[bold green]Thinking..."
    # Track spinner in session so we can start/stop
    # during confirmation steps
    session.spinner = ui.console.status(msg, spinner=ui.spinner)
    session.spinner.start()

    if session.undo_initialized:
        commit_for_undo("user")

    try:
        try:
            await agent.process_request(res, compact=compact)
            if session.undo_initialized:
                commit_for_undo("sidekick")
        except (KeyboardInterrupt, asyncio.CancelledError):
            ui.warning("Request cancelled")
            ui.line()
    finally:
        session.spinner.stop()


async def get_user_input():
    placeholder = ui.formatted_text(
        (
            "<darkgrey>"
            "<bold>Enter</bold> to submit, "
            "<bold>Esc + Enter</bold> for new line, "
            "<bold>/help</bold> for commands"
            "</darkgrey>"
        )
    )
    session = PromptSession("λ ", placeholder=placeholder)
    try:
        res = await session.prompt_async(key_bindings=kb, multiline=True)
        return res.strip()
    except (EOFError, KeyboardInterrupt):
        return


async def interactive_shell():
    command_handler = CommandHandler(agent, process_request)
    while True:
        # Need to use patched stdout to allow for multiline input
        # while in async mode.
        with patch_stdout():
            res = await get_user_input()

        if res is None:
            break

        res = res.strip()

        if res.lower() == "exit":
            break

        # Check if it's a command handled by CommandHandler
        if res.startswith("/"):
            command_handled = await command_handler.handle(res)
            if command_handled:
                continue

        # All output must be done after patched output otherwise
        # ANSI escape sequences will be printed.
        await process_request(res)


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
    logfire_enabled: bool = typer.Option(False, "--logfire", help="Enable Logfire tracing."),
    no_telemetry: bool = typer.Option(
        False, "--no-telemetry", help="Disable telemetry collection."
    ),
):
    """Main entry point for the Sidekick CLI."""
    if version:
        typer.echo(config.VERSION)
        return

    ui.show_banner()

    has_update, latest_version, update_message = check_for_updates()
    if has_update:
        ui.warning(update_message)

    if no_telemetry:
        session.telemetry_enabled = False

    try:

        async def run_app():
            await setup(agent)

            if logfire_enabled:
                logfire.configure(console=False)
                ui.status("Enabling Logfire tracing")

            if session.undo_initialized:
                # Create initial commit for user state
                commit_for_undo("user")

            ui.status("Starting interactive shell")
            ui.success("Go kick some ass\n")

            try:
                await interactive_shell()
            finally:
                cleanup_session()

        # Run the async application
        asyncio.run(run_app())
    except Exception as e:
        if session.telemetry_enabled:
            telemetry.capture_exception(e)
        raise e


if __name__ == "__main__":
    app()
