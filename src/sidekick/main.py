import asyncio

import logfire
import typer
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession

from sidekick import config, session
from sidekick.agents.main import MainAgent
from sidekick.utils import telemetry, ui
from sidekick.utils.mcp import stop_mcp_servers
from sidekick.utils.setup import setup
from sidekick.utils.system import check_for_updates, cleanup_session
from sidekick.utils.undo import commit_for_undo, init_undo_system, perform_undo

app = typer.Typer(help=config.NAME)
agent = MainAgent()


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
        except (KeyboardInterrupt, asyncio.CancelledError):
            ui.warning("Request cancelled")
            ui.line()

        if session.undo_initialized:
            commit_for_undo("sidekick")
    finally:
        session.spinner.stop()


async def get_user_input():
    session = PromptSession("λ ")
    try:
        res = await session.prompt_async(multiline=True)
        return res.strip()
    except (EOFError, KeyboardInterrupt):
        return


async def interactive_shell():
    try:
        while True:
            # Need to use patched stdout to allow for multiline input
            # while in async mode.
            with patch_stdout():
                res = await get_user_input()

            if res is None:
                # Ensure cleanup happens on normal exit
                cleanup_session()
                break

            res = res.strip()
            cmd = res.lower()

            if cmd == "exit":
                break

            if cmd == "/yolo":
                session.yolo = not session.yolo
                if session.yolo:
                    ui.success("Ooh shit, its YOLO time!\n")
                else:
                    ui.status("Pfft, boring...\n")
                continue

            if cmd == "/dump":
                ui.dump_messages()
                continue

            if cmd == "/clear":
                ui.console.clear()
                ui.show_banner()
                session.messages = []
                continue

            if cmd == "/help":
                ui.show_help()
                continue

            if cmd == "/undo":
                success, message = perform_undo()
                if success:
                    ui.success(message)
                else:
                    ui.warning(message)
                continue

            if cmd == "/compact":
                await process_request(
                    (
                        "Summarize the context of this conversation into a concise "
                        "breakdown, ensuring it contain's enough key details for "
                        "future conversations."
                    ),
                    compact=True,
                )
                continue

            if cmd.startswith("/model"):
                try:
                    model = cmd.split(" ")[1]
                    agent.switch_model(model)
                    continue
                except IndexError:
                    ui.show_models()
                    continue

            # All output must be done after patched output otherwise
            # ANSI escape sequences will be printed.
            # Process only non-empty requests
            if res:
                await process_request(res)
    finally:
        await stop_mcp_servers()


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
            # Setup all components in the specified order
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
