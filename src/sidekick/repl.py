import asyncio
from asyncio.exceptions import CancelledError

from prompt_toolkit import PromptSession
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings

from sidekick import session, ui
from sidekick.agents import main as agent


kb = KeyBindings()
placeholder = ui.formatted_text(
    (
        "<darkgrey>"
        "<bold>Enter</bold> to submit, "
        "<bold>Esc + Enter</bold> for new line, "
        "<bold>/help</bold> for commands"
        "</darkgrey>"
    )
)
ps = PromptSession("λ ", key_bindings=kb, placeholder=placeholder)
ps.app.ttimeoutlen = 0.05  # Shorten escape sequence timeout
session.current_task: asyncio.Task | None = None


def _print(message_type: str, message: str):
    """Handle messages from the agent."""
    if message_type in ["info", "status"]:
        run_in_terminal(lambda: ui.status(message))
    elif message_type == "warning":
        run_in_terminal(lambda: ui.warning(message))
    elif message_type == "error":
        run_in_terminal(lambda: ui.error(message))
    elif message_type == "agent":
        run_in_terminal(lambda: ui.agent(message))
    else:
        run_in_terminal(lambda: ui.muted(message))


@kb.add("escape", eager=True)
def _cancel(event):
    """Kill the running agent task, if any."""
    if session.current_task and not session.current_task.done():
        session.current_task.cancel()
        event.app.invalidate()


@kb.add("enter")
def _submit(event):
    """Submit the current buffer."""
    event.current_buffer.validate_and_handle()


@kb.add("c-o")  # ctrl+o
def _newline(event):
    """Insert a newline character."""
    event.current_buffer.insert_text("\n")


def _tool_handler(part, node):
    _print("info", f"Tool({part.tool_name})")


async def process_request(text: str):
    """Process input using the agent, handling cancellation safely."""
    msg = "[bold green]Thinking..."
    # Track spinner in session so we can start/stop
    # during confirmation steps
    session.spinner = await run_in_terminal(lambda: ui.console.status(msg, spinner=ui.spinner))
    session.spinner.start()

    try:
        res = await agent.process_request(
            "openai:gpt-4o", text, tool_callback=_tool_handler,
        )
        _print("agent", res.result.output)
    except CancelledError:
        _print("muted", "Request cancelled")
    finally:
        session.spinner.stop()
        session.current_task = None


async def repl():
    _print("info", "Starting up.")
    instance = agent.get_or_create_agent(session.current_model)
    async with instance.run_mcp_servers():
        _print("info", "MCP Servers started.")
        while True:
            try:
                # Ensure prompt is displayed correctly even after async output
                await run_in_terminal(lambda: ps.app.invalidate())
                line = await ps.prompt_async(key_bindings=kb, multiline=True)
            except (EOFError, KeyboardInterrupt):
                _print("info", "Thanks for all the fish...")
                break

            if not line.strip():
                continue

            # Check if another task is already running
            if session.current_task and not session.current_task.done():
                _print("muted", "Agent is busy, press esc to interrupt.")
                continue

            session.current_task = get_app().create_background_task(process_request(line))
