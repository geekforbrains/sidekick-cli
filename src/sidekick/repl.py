import asyncio
import json
from asyncio.exceptions import CancelledError
from datetime import datetime, timezone

from prompt_toolkit import PromptSession
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from pydantic_ai.messages import ModelRequest, ToolReturnPart

from sidekick import config, session, ui
from sidekick.agents import main as agent
from sidekick.exceptions import SidekickAbort
from sidekick.utils.helpers import ext_to_lang, key_to_title, render_file_diff

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


def _patch_tool_message(tool_name, tool_call_id):
    """
    If a tool is cancelled, we need to patch a response otherwise
    some models will throw an error.
    """
    session.messages.append(
        ModelRequest(
            parts=[
                ToolReturnPart(
                    tool_name=tool_name,
                    content="Operation aborted by user.",
                    tool_call_id=tool_call_id,
                    timestamp=datetime.now(timezone.utc),
                    part_kind="tool-return",
                )
            ],
            kind="request",
        )
    )


def _parse_args(args):
    """
    Parse tool arguments from a JSON string or dictionary.

    Args:
        args (str or dict): A JSON-formatted string or a dictionary containing tool arguments.

    Returns:
        dict: The parsed arguments.

    Raises:
        ValueError: If 'args' is not a string or dictionary, or if the string is not valid JSON.
    """
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON: {args}")
    elif isinstance(args, dict):
        return args
    else:
        raise ValueError(f"Invalid args type: {type(args)}")


def _get_tool_title(tool_name):
    """
    Checks if the tool exists within this system. If it does
    it return "Tool" otherwise assumed to be an MCP so returns "MCP"
    """
    if tool_name in config.INTERNAL_TOOLS:
        return f"Tool({tool_name})"
    else:
        return f"MCP({tool_name})"


def _create_code_block(filepath: str, content: str) -> ui.Markdown:
    """
    Create a code block for the given file path and content.

    Args:
        filepath (str): The path to the file.
        content (str): The content of the file.

    Returns:
        Markdown: A Markdown object representing the code block.
    """
    lang = ext_to_lang(filepath)
    code_block = f"```{lang}\n{content}\n```"
    return ui.markdown(code_block)


def _render_args(tool_name, args):
    """
    Render the tool arguments for a given tool.

    """
    # Show diff between `target` and `patch` on file updates
    if tool_name == "update_file":
        return render_file_diff(args["target"], args["patch"], ui.colors)

    # Show file content on read_file
    elif tool_name == "write_file":
        return _create_code_block(args["filepath"], args["content"])

    # Default to showing key and value on new line
    content = ""
    for key, value in args.items():
        if isinstance(value, list):
            content += f"{key_to_title(key)}:\n"
            for item in value:
                content += f"  - {item}\n"
            content += "\n"
        else:
            # If string length is over 200 characters
            # split to new line
            # content += f"{key.title()}:\n{value}\n\n"
            value = str(value)
            content += f"{key_to_title(key)}:"
            if len(value) > 200:
                content += f"\n{value}\n\n"
            else:
                content += f" {value}\n\n"
    return content.strip()


def _log_mcp(title, args):
    """Display MCP tool with its arguments."""
    if not args:
        return

    ui.status(title)
    for key, value in args.items():
        if isinstance(value, list):
            value = ", ".join(value)
        ui.muted(f"{key}: {value}", spaces=4)


def _tool_confirm(tool_call, node):
    title = _get_tool_title(tool_call.tool_name)
    args = _parse_args(tool_call.args)

    # If we're skipping confirmation on this tool, log its output if MCP
    if (
        session.yolo
        or tool_call.tool_name in session.tool_ignore
        # or tool_call.tool_name in session.user_config["settings"]["tool_ignore"]
    ):
        if tool_call.tool_name not in config.INTERNAL_TOOLS:
            _log_mcp(title, args)
        return

    session.spinner.stop()
    content = _render_args(tool_call.tool_name, args)
    filepath = args.get("filepath")

    # Set bottom padding to 0 if filepath is not None
    bottom_padding = 0 if filepath else 1

    ui.panel(title, content, bottom=bottom_padding, border_style=ui.colors.warning)

    # If tool call has filepath, show it under panel
    if filepath:
        ui.show_usage(f"File: {filepath}")

    print("  1. Yes (default)")
    print("  2. Yes, and don't ask again for commands like this")
    print("  3. No, and tell Sidekick what to do differently")
    resp = input("  Choose an option [1/2/3]: ").strip() or "1"

    if resp == "2":
        session.tool_ignore.append(tool_call.tool_name)
    elif resp == "3":
        raise SidekickAbort("User aborted.")

    ui.line()  # Add line after user input
    session.spinner.start()


async def _tool_handler(part, node):
    _print("info", f"Tool({part.tool_name})")
    session.spinner.stop()
    try:
        await run_in_terminal(lambda: _tool_confirm(part, node))
    except SidekickAbort:
        _patch_tool_message(part.tool_name, part.tool_call_id)
        raise  # Let caller handle cancellation
    session.spinner.start()


async def process_request(text: str):
    """Process input using the agent, handling cancellation safely."""
    msg = "[bold green]Thinking..."
    # Track spinner in session so we can start/stop
    # during confirmation steps
    session.spinner = await run_in_terminal(lambda: ui.console.status(msg, spinner=ui.spinner))
    session.spinner.start()

    try:
        res = await agent.process_request(
            "openai:gpt-4o",
            text,
            tool_callback=_tool_handler,
        )
        _print("agent", res.result.output)
    except CancelledError:
        _print("muted", "Request cancelled")
    except SidekickAbort:
        _print("muted", "Operation aborted.")
    finally:
        session.spinner.stop()
        session.current_task = None


async def repl():
    _print("info", "Starting up.")
    instance = agent.get_or_create_agent(session.current_model)
    _print("info", "Booting MPC servers...")
    async with instance.run_mcp_servers():
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
