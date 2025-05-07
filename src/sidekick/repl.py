import json
from asyncio.exceptions import CancelledError
from datetime import datetime, timezone

from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.application.current import get_app
from pydantic_ai.messages import ModelRequest, ToolReturnPart

from sidekick import config, session, ui
from sidekick.agents import main as agent
from sidekick.exceptions import SidekickAbort
from sidekick.utils import user_config
from sidekick.utils.helpers import ext_to_lang, key_to_title, render_file_diff
from sidekick.utils.undo import perform_undo


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

    ui.info(title)
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
        or tprintool_call.tool_name in session.tool_ignore
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
    ui.info(f"Tool({part.tool_name})")
    session.spinner.stop()
    try:
        await run_in_terminal(lambda: _tool_confirm(part, node))
    except SidekickAbort:
        _patch_tool_message(part.tool_name, part.tool_call_id)
        raise  # Let caller handle cancellation
    session.spinner.start()


def _toggle_yolo():
    session.yolo = not session.yolo
    if session.yolo:
        ui.success("Ooh shit, its YOLO time!\n")
    else:
        ui.info("Pfft, boring...\n")


def _dump_messages():
    ui.dump_messages()


def _clear_screen():
    ui.console.clear()
    ui.show_banner()
    session.messages = []


def _show_help():
    ui.help()


def _perform_undo():
    success, message = perform_undo()
    if success:
        ui.success(message)
    else:
        ui.warning(message)


async def _compact_context():
    """Get the current agent, create a summary of contenxt, and trim message history"""
    await process_request("Summarize the conversation so far", output=False)
    ui.success("Context history has been summarized and truncated.")
    session.messages = session.messages[-2:]


def _handle_model_command(model_index: int = None, action: str = None):
    if model_index:
        models = list(config.MODELS.keys())
        model = models[int(model_index)]
        session.current_model = model
        if action == "default":
            user_config.set_default_model(model)
            ui.muted("Updating default model")
        return "restart"
    else:
        ui.show_models()


async def _handle_command(command: str) -> bool:
    """
    Handles a command string.

    Args:
        command: The command string entered by the user.

    Returns:
        True if the command was handled, False otherwise.
    """
    cmd_lower = command.lower()
    parts = cmd_lower.split()
    base_command = parts[0]

    COMMANDS = {
        "/yolo": _toggle_yolo,
        "/dump": _dump_messages,
        "/clear": _clear_screen,
        "/help": _show_help,
        "/undo": _perform_undo,
        "/compact": _compact_context,
        "/model": _handle_model_command,
    }

    if base_command in COMMANDS:
        if base_command == "/compact":
            return await _compact_context()
        else:
            return COMMANDS[base_command](*parts[1:])
    else:
        ui.errro(f"Unknown command: {command}")


async def process_request(text: str, output: bool = True):
    """Process input using the agent, handling cancellation safely."""
    await ui.spinner(True)
    try:
        res = await agent.process_request(
            session.current_model,
            text,
            tool_callback=_tool_handler,
        )
        if output:
            ui.agent(res.result.output)
    except CancelledError:
        ui.muted("Request cancelled")
    except SidekickAbort:
        ui.muted("Operation aborted.")
    except Exception as e:
        ui.muted(str(e))
    finally:
        await ui.spinner(False)
        session.current_task = None


async def repl():
    action = None

    ui.info(f"Using model {session.current_model}")
    instance = agent.get_or_create_agent(session.current_model)

    ui.info("Attaching MCP servers")
    async with instance.run_mcp_servers():
        while True:
            try:
                line = await ui.multiline_input()
            except (EOFError, KeyboardInterrupt):
                break

            if not line:
                continue

            if line.lower() in ["exit", "quit"]:
                break

            if line.startswith("/"):
                action = await _handle_command(line)
                if action == "restart":
                    break
                continue

            # Check if another task is already running
            if session.current_task and not session.current_task.done():
                ui.muted("Agent is busy, press esc to interrupt.")
                continue

            session.current_task = get_app().create_background_task(process_request(line))

    if action == "restart":
        await repl()
    else:
        ui.info("Thanks for all the fish.")
