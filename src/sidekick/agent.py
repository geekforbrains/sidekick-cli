import json

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from sidekick import session, ui
from sidekick.tools import TOOLS

fetch = MCPServerStdio(
    "uvx",
    args=[
        "mcp-server-fetch",
    ],
)

brave_search = MCPServerStdio(
    "npx",
    args=[
        "-y",
        "@modelcontextprotocol/server-brave-search",
    ],
    env={
        "BRAVE_API_KEY": "BSANgzuH-zsMsCsZ371rHjhBkYaQm5j",
    },
)


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
    """Get or create an agent instance for the current model."""
    if session.current_model not in session.agents:
        session.agents[session.current_model] = Agent(
            model=session.current_model,
            system_prompt=_get_prompt("system"),
            tools=TOOLS,
            mcp_servers=[fetch, brave_search],
        )
    return session.agents[session.current_model]


async def process_request(message: str):
    """Process a user request with the agent."""
    agent = get_or_create_agent()
    mh = session.messages.copy()
    async with agent.iter(message, message_history=mh) as agent_run:
        async for node in agent_run:
            await _process_node(node)
        return agent_run.result.output
