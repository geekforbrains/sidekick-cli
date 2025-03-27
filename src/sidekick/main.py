import asyncio

import logfire
import typer
from dotenv import load_dotenv
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession

from sidekick import config, session
from sidekick.agents.main import MainAgent
from sidekick.utils import ui

load_dotenv()
app = typer.Typer(help=config.name)
logfire.configure(console=False)
agent = MainAgent()


async def process_request(res):
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

        res = res.strip()
        cmd = res.lower()

        if cmd == "exit":
            break

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
        await process_request(res)


@app.command()
def main():
    ui.show_banner()
    asyncio.run(interactive_shell())


if __name__ == "__main__":
    app()
