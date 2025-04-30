from pydantic_ai import Agent

from sidekick import session
from sidekick.tools.run_command import run_command
from sidekick.utils.mcp import get_mcp_servers


async def _process_node(node, tool_callback):
    if hasattr(node, "request"):
        session.messages.append(node.request)

    if hasattr(node, "model_response"):
        session.messages.append(node.model_response)
        for part in node.model_response.parts:
            if part.part_kind == "tool-call" and tool_callback:
                await tool_callback(part, node)


def get_or_create_agent(model):
    if not hasattr(session.agents, model):
        session.agents[model] = Agent(
            model=model,
            tools=[
                # read_file,
                run_command,
                # update_file,
                # write_file,
            ],
            mcp_servers=get_mcp_servers(),
        )
    return session.agents[model]


async def process_request(model: str, message: str, tool_callback: callable = None):
    agent = get_or_create_agent(model)
    mh = session.messages.copy()
    async with agent.iter(message, message_history=mh) as agent_run:
        async for node in agent_run:
            await _process_node(node, tool_callback)
        return agent_run
