import asyncio
from pathlib import Path
from typing import Optional

from pydantic_ai import Agent

from sidekick import ui
from sidekick.constants import MODELS
from sidekick.deps import ToolDeps
from sidekick.mcp import MCPAgent, load_mcp_servers
from sidekick.session import session
from sidekick.tools import TOOLS
from sidekick.utils.display import TOOL_DISPLAY_NAMES, format_tool_name


def _get_prompt(name: str) -> str:
    """Return contents of .src/sidekick/prompts/system.txt."""
    try:
        prompt_path = Path(__file__).parent / "prompts" / f"{name}.txt"
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return f"Error: Prompt file '{name}.txt' not found"


async def _format_tool_display(tool_name: str, args: dict):
    """Format and display tool call information."""
    display_name = format_tool_name(tool_name)

    if tool_name in TOOL_DISPLAY_NAMES:
        primary_arg = None
        if tool_name in ["read_file", "write_file", "update_file"] and "filepath" in args:
            primary_arg = args["filepath"]
        elif tool_name == "run_command" and "command" in args:
            primary_arg = args["command"]
        elif tool_name == "git_add" and "files" in args:
            primary_arg = args["files"]
        elif tool_name == "git_commit" and "message" in args:
            # Show first line of commit message
            message = args["message"]
            first_line = message.split("\n")[0]
            if len(first_line) > 50:
                first_line = first_line[:47] + "..."
            primary_arg = f'"{first_line}"'
        elif tool_name in ["search_files", "search_dirs"] and "pattern" in args:
            primary_arg = f'"{args["pattern"]}"'
        elif tool_name == "search_content" and "text_pattern" in args:
            primary_arg = f'"{args["text_pattern"]}"'
        elif tool_name == "list_directory":
            path = args.get("path", ".")
            primary_arg = f'"{path}"'

        if primary_arg:
            ui.info(f"{display_name}({primary_arg})")
        else:
            ui.info(f"{display_name}(...)")
    else:
        ui.info(display_name)
        for key, value in args.items():
            if isinstance(value, str):
                value = value.strip()
            ui.info(f"  {key}: {value}")


async def _track_tool_request(part):
    """Track that a tool was requested."""
    # Store the tool request details for later display
    if not hasattr(session, "pending_tools"):
        session.pending_tools = {}

    session.pending_tools[part.tool_call_id] = {"name": part.tool_name, "args": part.args_as_dict()}


async def _cleanup_pending_tools():
    """Clean up any pending tool requests."""
    if hasattr(session, "pending_tools"):
        session.pending_tools.clear()


async def _process_node(node):
    if hasattr(node, "request"):
        session.messages.append(node.request)

        # Handle retry prompts
        for part in node.request.parts:
            if part.part_kind == "retry-prompt":
                if session.spinner:
                    session.spinner.stop()
                error_msg = (
                    part.content
                    if hasattr(part, "content") and isinstance(part.content, str)
                    else "Trying a different approach"
                )
                ui.muted(f"{error_msg}")
                if session.spinner:
                    session.spinner.start()

            # Handle tool returns - show status only for successful executions
            elif part.part_kind == "tool-return" and hasattr(session, "pending_tools"):
                tool_id = getattr(part, "tool_call_id", None)
                if tool_id and tool_id in session.pending_tools:
                    # Tool was executed successfully, show the status
                    tool_info = session.pending_tools[tool_id]

                    if session.spinner:
                        session.spinner.stop()

                    # Track usage
                    tool_name = tool_info["name"]
                    if tool_name not in session.tool_usage:
                        session.tool_usage[tool_name] = 0
                    session.tool_usage[tool_name] += 1

                    # Display status
                    await _format_tool_display(tool_name, tool_info["args"])

                    if session.spinner:
                        session.spinner.start()

                    # Clean up
                    del session.pending_tools[tool_id]

    if hasattr(node, "model_response"):
        session.messages.append(node.model_response)

        # Track tool requests (don't display yet)
        tool_calls = [part for part in node.model_response.parts if part.part_kind == "tool-call"]
        for tool_call in tool_calls:
            await _track_tool_request(tool_call)


def _calculate_usage_costs(usage):
    """Calculate usage costs from agent run usage data."""
    # Get cached tokens from details if available
    cached_tokens = 0
    if hasattr(usage, "details") and usage.details:
        for detail in usage.details:
            if hasattr(detail, "cached_tokens"):
                cached_tokens += detail.cached_tokens

    # Calculate token counts
    input_tokens = usage.request_tokens
    non_cached_input = input_tokens - cached_tokens
    output_tokens = usage.response_tokens

    # Get pricing for current model (fallback to first model if not found)
    model_ids = list(MODELS.keys())
    pricing = MODELS.get(session.current_model, MODELS[model_ids[0]])["pricing"]

    # Calculate costs (prices are per 1M tokens)
    input_cost = non_cached_input / 1_000_000 * pricing["input"]
    cached_cost = cached_tokens / 1_000_000 * pricing["cached_input"]
    output_cost = output_tokens / 1_000_000 * pricing["output"]
    request_cost = input_cost + cached_cost + output_cost

    return {
        "requests": usage.requests,
        "input_tokens": input_tokens,
        "cached_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "cached_cost": cached_cost,
        "output_cost": output_cost,
        "request_cost": request_cost,
        "total_cost": session.total_cost + request_cost,
    }


def get_or_create_agent():
    """Get or create an MCP agent instance for the current model."""
    if session.current_model not in session.agents:
        base_agent = Agent(
            model=session.current_model,
            system_prompt=_get_prompt("system"),
            tools=TOOLS,
            mcp_servers=load_mcp_servers(),
            deps_type=ToolDeps,
        )
        session.agents[session.current_model] = MCPAgent(base_agent)
    return session.agents[session.current_model]


def _create_confirmation_callback():
    """Create a confirmation callback for tools."""

    async def confirm(title: str, preview: any, footer: Optional[str] = None) -> bool:
        tool_name = title.split(":")[0].strip() if ":" in title else title

        # Check if confirmations are disabled globally or for this tool
        if not session.confirmation_enabled or tool_name in session.disabled_confirmations:
            return True

        # Stop spinner before showing anything
        if session.spinner:
            session.spinner.stop()

        # Display the tool preview
        ui.display_tool_panel(preview, title, footer)

        # Show confirmation options
        options_content = [
            "Options:",
            "  y - Yes, execute this tool",
            "  a - Always allow this tool",
            "  n - No, cancel this execution",
        ]
        ui.display_confirmation_panel("\n".join(options_content))

        while True:
            choice = (
                ui.console.input(
                    f"  [{ui.colors.warning}]Continue?[/{ui.colors.warning}] [y/a/n] (default: y): "
                )
                .lower()
                .strip()
            )

            if choice == "" or choice in ["y", "yes"]:
                ui.console.print()
                if session.spinner:
                    session.spinner.start()
                return True
            elif choice in ["a", "always"]:
                session.disabled_confirmations.add(tool_name)
                ui.console.print()
                if session.spinner:
                    session.spinner.start()
                return True
            elif choice in ["n", "no"]:
                ui.console.print()
                # Don't restart spinner on cancel
                return False
            else:
                ui.console.print(
                    "  Invalid choice. Please enter y, a, or n.", style=ui.colors.error
                )

    return confirm


async def process_request(message: str):
    """Process a user request with the agent."""
    mcp_agent = get_or_create_agent()
    agent = mcp_agent.agent

    mh = session.messages.copy()

    # Always provide the confirmation callback - tools will check if they need to use it
    deps = ToolDeps(confirm_action=_create_confirmation_callback())

    try:
        async with agent.iter(message, deps=deps, message_history=mh) as agent_run:
            async for node in agent_run:
                await _process_node(node)

            # Capture usage data and calculate costs
            usage = agent_run.usage()
            if usage:
                session.last_usage = _calculate_usage_costs(usage)
                session.total_tokens += usage.total_tokens
                session.total_cost = session.last_usage["total_cost"]

            return agent_run.result.output
    except asyncio.CancelledError as e:
        # Check if this was a user-initiated tool cancellation
        if str(e) == "Tool execution cancelled by user":
            ui.warning("Tool execution cancelled")
            return None
        raise
    finally:
        # Clean up any pending tools that didn't execute
        await _cleanup_pending_tools()
