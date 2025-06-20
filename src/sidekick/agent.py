import asyncio
from pathlib import Path

from pydantic_ai import Agent

from sidekick import ui
from sidekick.config import MODELS
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


async def _handle_run_command_approval(command_string: str, args: dict) -> str:
    """Handle approval for run_command tool specifically."""
    from sidekick.utils.command_parser import extract_commands, is_command_allowed

    # Check if the command is already allowed
    if is_command_allowed(command_string, session.allowed_commands):
        return "allowed"

    # Ask for approval
    response = await ui.confirm_tool_call("run_command", args)

    if response == "always":
        # Add individual commands to allowed list
        commands = extract_commands(command_string)
        session.allowed_commands.update(commands)

    return response


async def _render_tool_call(part):
    """Print the output of a tool call and get confirmation."""
    if session.spinner:
        session.spinner.stop()

    args = part.args_as_dict()

    if session.confirmation_enabled:
        response = None

        # Special handling for run_command tool
        if part.tool_name == "run_command" and "command" in args:
            response = await _handle_run_command_approval(args["command"], args)
        # Regular tool handling
        elif part.tool_name not in session.skip_confirmations:
            response = await ui.confirm_tool_call(part.tool_name, args)
            if response == "always":
                session.skip_confirmations.add(part.tool_name)

        if response == "no":
            raise asyncio.CancelledError("Tool execution cancelled by user")

    # Track tool usage
    if part.tool_name not in session.tool_usage:
        session.tool_usage[part.tool_name] = 0
    session.tool_usage[part.tool_name] += 1

    await _format_tool_display(part.tool_name, args)

    if session.spinner:
        session.spinner.start()


async def _handle_tool_cancellation(tool_calls):
    """Create tool return parts for cancelled tool calls."""
    from pydantic_ai import messages

    cancelled_parts = []
    for tool_call in tool_calls:
        cancelled_parts.append(
            messages.ToolReturnPart(
                tool_name=tool_call.tool_name,
                content="Tool execution cancelled by user",
                tool_call_id=tool_call.tool_call_id,
            )
        )

    if cancelled_parts:
        session.messages.append(messages.ModelRequest(parts=cancelled_parts))


async def _process_node(node):
    if hasattr(node, "request"):
        session.messages.append(node.request)

    if hasattr(node, "model_response"):
        session.messages.append(node.model_response)
        tool_calls = [part for part in node.model_response.parts if part.part_kind == "tool-call"]

        cancelled = False
        try:
            for tool_call in tool_calls:
                await _render_tool_call(tool_call)
        except asyncio.CancelledError as e:
            cancelled = True
            raise e
        finally:
            if cancelled and tool_calls:
                await _handle_tool_cancellation(tool_calls)


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
        )
        session.agents[session.current_model] = MCPAgent(base_agent)
    return session.agents[session.current_model]


async def process_request(message: str):
    """Process a user request with the agent."""
    mcp_agent = get_or_create_agent()
    agent = mcp_agent.agent

    mh = session.messages.copy()

    try:
        async with agent.iter(message, message_history=mh) as agent_run:
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
            await ui.warning("Tool execution cancelled")
            return None
        raise
