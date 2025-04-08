import asyncio

import logfire
import typer
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession

from sidekick import config, session
from sidekick.agents.main import MainAgent
from sidekick.utils import telemetry, ui
from sidekick.utils.setup import setup
from sidekick.utils.system import cleanup_session
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
        await agent.process_request(res, compact=compact)

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


@app.command()
def main(
    logfire_enabled: bool = typer.Option(False, "--logfire", help="Enable Logfire tracing."),
    no_telemetry: bool = typer.Option(
        False, "--no-telemetry", help="Disable telemetry collection."
    ),
):
    """Main entry point for the Sidekick CLI."""
    ui.show_banner()

    if no_telemetry:
        session.telemetry_enabled = False
        ui.status("Telemetry disabled, skipping")
    else:
        ui.status("Setting up telemetry")
        telemetry.setup()

    try:
        ui.status("Setting up config")
        setup()

        # Set the current model from user config
        if not session.user_config.get("default_model"):
            raise ValueError("No default model found in config at [bold]~/.config/sidekick.json")
        session.current_model = session.user_config["default_model"]

        if logfire_enabled:
            logfire.configure(console=False)
            ui.status("Enabling Logfire tracing")

        # Initialize undo system
        ui.status("Initializing undo system")
        session.undo_initialized = init_undo_system()
        if session.undo_initialized:
            # Create initial commit for user state
            commit_for_undo("user")

        ui.status("Starting interactive shell")
        ui.success("Go kick some ass\n")

        try:
            asyncio.run(interactive_shell())
        finally:
            cleanup_session()
    except Exception as e:
        telemetry.capture_exception(e)
        raise e


if __name__ == "__main__":
    app()
