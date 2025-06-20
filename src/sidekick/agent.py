import asyncio

from pydantic_ai import Agent

from sidekick import session, ui
from sidekick.mcp import MCPAgent, get_configured_servers
from sidekick.tools import TOOLS


def _get_prompt(name: str) -> str:
    """Return contents of .src/sidekick/prompts/system.txt."""
    with open(f"./src/sidekick/prompts/{name}.txt", "r", encoding="utf-8") as file:
        return file.read().strip()


async def _render_tool_call(part):
    """Print the output of a tool call and get confirmation."""
    if session.spinner:
        session.spinner.stop()

    args = part.args_as_dict()

    # Check if confirmations are enabled and if we should ask
    if session.confirmation_enabled and part.tool_name not in session.skip_confirmations:
        # Get user confirmation
        response = await ui.confirm_tool_call(part.tool_name, args)

        if response == "no":
            # User cancelled - raise exception to stop execution
            raise asyncio.CancelledError("Tool execution cancelled by user")
        elif response == "always":
            # Add to skip list for future calls
            session.skip_confirmations.add(part.tool_name)
    else:
        # Just display the tool info without confirmation
        await ui.info(f"Tool({part.tool_name})")
        for key, value in args.items():
            if isinstance(value, str):
                value = value.strip()
            await ui.info(f"- {key}: {value}")

    if session.spinner:
        session.spinner.start()


async def _process_node(node):
    if hasattr(node, "request"):
        session.messages.append(node.request)

    if hasattr(node, "model_response"):
        session.messages.append(node.model_response)
        for part in node.model_response.parts:
            if part.part_kind == "tool-call":
                await _render_tool_call(part)


def get_or_create_agent():
    """Get or create an MCP agent instance for the current model."""
    if session.current_model not in session.agents:
        base_agent = Agent(
            model=session.current_model,
            system_prompt=_get_prompt("system"),
            tools=TOOLS,
            mcp_servers=get_configured_servers(),
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
            return agent_run.result.output
    except asyncio.CancelledError as e:
        # Check if this was a user-initiated tool cancellation
        if str(e) == "Tool execution cancelled by user":
            await ui.warning("Tool execution cancelled")
            return None
        raise
