import asyncio

import logfire
import typer
from dotenv import load_dotenv
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession

from sidekick import config, session
from sidekick.agents.main import MainAgent
from sidekick.utils import ui
from sidekick.utils.setup import setup

load_dotenv()
app = typer.Typer(help=config.NAME)
agent = MainAgent()


async def process_request(res):
    ui.line()
    msg = "[bold green]Thinking..."
    # Track spinner in session so we can start/stop
    # during confirmation steps
    session.spinner = ui.console.status(msg, spinner=ui.spinner)
    session.spinner.start()
    try:
        res = await agent.process_request(res)
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

        # Debug commands for UI
        if cmd.startswith("/debug"):
            try:
                mode = cmd.split(" ")[-1]
                if mode == "error":
                    ui.error("This is an error!")
            except IndexError:
                ui.error("Invalid debug command.")
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
def main(logfire_enabled: bool = typer.Option(False, "--logfire", help="Enable Logfire tracing.")):
    """Main entry point for the Sidekick CLI."""
    ui.show_banner()
    setup()

    # Set the current model from user config
    if not session.user_config.get("default_model"):
        raise ValueError("No default model found in config at [bold]~/.config/sidekick.json")
    session.current_model = session.user_config["default_model"]

    if logfire_enabled:
        logfire.configure(console=False)
        ui.status("Logfire enabled.\n")
    asyncio.run(interactive_shell())


if __name__ == "__main__":
    app()
