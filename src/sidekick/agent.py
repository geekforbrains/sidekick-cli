import asyncio
import json

from pydantic_ai import Agent

from sidekick import session, ui
from sidekick.tools import TOOLS
from sidekick.utils.mcp import get_configured_servers
from sidekick.resilient_agent import ResilientAgent


def _get_prompt(name: str) -> str:
    """Return contents of .src/sidekick/prompts/system.txt."""
    with open(f"./src/sidekick/prompts/{name}.txt", "r", encoding="utf-8") as file:
        return file.read().strip()


async def _render_tool_call(part):
    """Print the output of a tool call."""
    if session.spinner:
        session.spinner.stop()
    args = json.loads(part.args)
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
    """Get or create a resilient agent instance for the current model."""
    if session.current_model not in session.agents:
        base_agent = Agent(
            model=session.current_model,
            system_prompt=_get_prompt("system"),
            tools=TOOLS,
            mcp_servers=get_configured_servers(),
        )
        session.agents[session.current_model] = ResilientAgent(base_agent)
    return session.agents[session.current_model]


async def process_request(message: str):
    """Process a user request with the agent."""
    resilient_agent = get_or_create_agent()
    agent = resilient_agent.agent
    
    mh = session.messages.copy()
    
    try:
        async with agent.iter(message, message_history=mh) as agent_run:
            async for node in agent_run:
                await _process_node(node)
            return agent_run.result.output
    except asyncio.CancelledError:
        raise