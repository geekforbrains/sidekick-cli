import json
from asyncio.exceptions import CancelledError

from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.application.current import get_app
from pydantic_ai.exceptions import UnexpectedModelBehavior

from sidekick import config, ui
from sidekick.agents import main as agent
from sidekick.agents.main import patch_tool_messages
from sidekick.core.state import StateManager
from sidekick.exceptions import SidekickAbort
from sidekick.utils import user_config
from sidekick.utils.helpers import ext_to_lang, key_to_title, render_file_diff
from sidekick.utils.undo import perform_undo


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


async def _log_mcp(title, args):
    """Display MCP tool with its arguments."""
    if not args:
        return

    await ui.info(title)
    for key, value in args.items():
        if isinstance(value, list):
            value = ", ".join(value)
        await ui.muted(f"{key}: {value}", spaces=4)


async def _tool_confirm(tool_call, node, state_manager: StateManager):
    title = _get_tool_title(tool_call.tool_name)
    args = _parse_args(tool_call.args)

    # If we're skipping confirmation on this tool, log its output if MCP
    if state_manager.session.yolo or tool_call.tool_name in state_manager.session.tool_ignore:
        if tool_call.tool_name not in config.INTERNAL_TOOLS:
            _log_mcp(title, args)
        return

    state_manager.session.spinner.stop()
    content = _render_args(tool_call.tool_name, args)
    filepath = args.get("filepath")

    await ui.tool_confirm(title, content, filepath=filepath)

    # If tool call has filepath, show it under panel
    if filepath:
        await ui.usage(f"File: {filepath}")

    await ui.print("  1. Yes (default)")
    await ui.print("  2. Yes, and don't ask again for commands like this")
    await ui.print("  3. No, and tell Sidekick what to do differently")
    resp = await ui.input(session_key="tool_confirm", pretext="  Choose an option [1/2/3]: ") or "1"

    if resp == "2":
        state_manager.session.tool_ignore.append(tool_call.tool_name)
    elif resp == "3":
        raise SidekickAbort("User aborted.")

    await ui.line()  # Add line after user input
    state_manager.session.spinner.start()


async def _tool_handler(part, node, state_manager: StateManager):
    await ui.info(f"Tool({part.tool_name})")
    state_manager.session.spinner.stop()

    try:
        # Use a synchronous function in run_in_terminal to avoid async deadlocks
        def confirm_func():
            title = _get_tool_title(part.tool_name)
            args = _parse_args(part.args)

            # Skip confirmation if needed
            if state_manager.session.yolo or part.tool_name in state_manager.session.tool_ignore:
                return False

            content = _render_args(part.tool_name, args)
            filepath = args.get("filepath")

            # Display styled confirmation panel using sync UI functions
            ui.sync_tool_confirm(title, content)
            if filepath:
                ui.sync_print(f"File: {filepath}", style=ui.colors.muted)

            ui.sync_print("  1. Yes (default)")
            ui.sync_print("  2. Yes, and don't ask again for commands like this")
            ui.sync_print("  3. No, and tell Sidekick what to do differently")
            resp = input("  Choose an option [1/2/3]: ").strip() or "1"

            if resp == "2":
                state_manager.session.tool_ignore.append(part.tool_name)
                return False
            elif resp == "3":
                return True  # Abort
            return False  # Continue

        # Run the confirmation in the terminal
        should_abort = await run_in_terminal(confirm_func)

        if should_abort:
            raise SidekickAbort("User aborted.")

    except SidekickAbort:
        patch_tool_messages("Operation aborted by user.", state_manager)
        raise
    finally:
        state_manager.session.spinner.start()


async def _toggle_yolo(state_manager: StateManager):
    state_manager.session.yolo = not state_manager.session.yolo
    if state_manager.session.yolo:
        await ui.success("Ooh shit, its YOLO time!\n")
    else:
        await ui.info("Pfft, boring...\n")


async def _dump_messages(state_manager: StateManager):
    await ui.dump_messages(state_manager.session.messages)


async def _clear_screen(state_manager: StateManager):
    await ui.clear()
    state_manager.session.messages = []


async def _show_help():
    await ui.help()


async def _perform_undo():
    success, message = perform_undo()
    if success:
        await ui.success(message)
    else:
        await ui.warning(message)


async def _compact_context(state_manager: StateManager):
    """Get the current agent, create a summary of contenxt, and trim message history"""
    await process_request("Summarize the conversation so far", state_manager, output=False)
    await ui.success("Context history has been summarized and truncated.")
    state_manager.session.messages = state_manager.session.messages[-2:]


async def _handle_model_command(
    state_manager: StateManager, model_index: int = None, action: str = None
):
    if model_index:
        models = list(config.MODELS.keys())
        model = models[int(model_index)]
        state_manager.session.current_model = model
        if action == "default":
            user_config.set_default_model(model)
            await ui.muted("Updating default model")
        return "restart"
    else:
        await ui.models()


async def _handle_command(command: str, state_manager: StateManager) -> bool:
    """
    Handles a command string.

    Args:
        command: The command string entered by the user.
        state_manager: The state manager instance.

    Returns:
        True if the command was handled, False otherwise.
    """
    cmd_lower = command.lower()
    parts = cmd_lower.split()
    base_command = parts[0]

    # Commands that need state_manager
    state_commands = {
        "/yolo": lambda: _toggle_yolo(state_manager),
        "/clear": lambda: _clear_screen(state_manager),
        "/compact": lambda: _compact_context(state_manager),
        "/dump": lambda: _dump_messages(state_manager),
        "/model": lambda *args: _handle_model_command(state_manager, *args),
    }

    # Commands that don't need state_manager
    static_commands = {
        "/help": _show_help,
        "/undo": _perform_undo,
    }

    if base_command in state_commands:
        if base_command == "/model":
            return await state_commands[base_command](*parts[1:])
        else:
            return await state_commands[base_command]()
    elif base_command in static_commands:
        return await static_commands[base_command]()
    else:
        await ui.error(f"Unknown command: {command}")


async def process_request(text: str, state_manager: StateManager, output: bool = True):
    """Process input using the agent, handling cancellation safely."""
    await ui.spinner(True)
    try:
        # Create a partial function that includes state_manager
        def tool_callback_with_state(part, node):
            return _tool_handler(part, node, state_manager)

        res = await agent.process_request(
            state_manager.session.current_model,
            text,
            state_manager,
            tool_callback=tool_callback_with_state,
        )
        if output:
            await ui.agent(res.result.output)
    except CancelledError:
        await ui.muted("Request cancelled")
    except SidekickAbort:
        await ui.muted("Operation aborted.")
    except UnexpectedModelBehavior as e:
        error_message = str(e)
        await ui.muted(error_message)
        patch_tool_messages(error_message, state_manager)
    except Exception as e:
        await ui.error(str(e))
    finally:
        await ui.spinner(False)
        state_manager.session.current_task = None

        # Force refresh of the multiline input prompt to restore placeholder
        if "multiline" in state_manager.session.input_sessions:
            await run_in_terminal(
                lambda: state_manager.session.input_sessions["multiline"].app.invalidate()
            )


async def repl(state_manager: StateManager):
    action = None

    await ui.info(f"Using model {state_manager.session.current_model}")
    instance = agent.get_or_create_agent(state_manager.session.current_model, state_manager)

    await ui.info("Attaching MCP servers")
    await ui.line()

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
                action = await _handle_command(line, state_manager)
                if action == "restart":
                    break
                continue

            # Check if another task is already running
            if state_manager.session.current_task and not state_manager.session.current_task.done():
                await ui.muted("Agent is busy, press esc to interrupt.")
                continue

            state_manager.session.current_task = get_app().create_background_task(
                process_request(line, state_manager)
            )

    if action == "restart":
        await repl(state_manager)
    else:
        await ui.info("Thanks for all the fish.")
