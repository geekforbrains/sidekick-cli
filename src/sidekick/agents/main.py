# import os
# import traceback
# from datetime import datetime, timezone

from pydantic_ai import Agent

from sidekick import session

# from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
# from pydantic_ai.mcp import MCPServerStdio
# from pydantic_ai.messages import ModelRequest, SystemPromptPart, ToolReturnPart


# from sidekick.tools import read_file, run_command, update_file, write_file
# from sidekick.utils import telemetry, ui, user_config
# from sidekick.utils.system import get_cwd, list_cwd
from sidekick.tools.run_command import run_command
from sidekick.utils.mcp import QuietMCPServer


servers = [
    QuietMCPServer(
        command="uvx",
        args=["mcp-server-fetch"],
    ),
    QuietMCPServer(
        command="uvx",
        args=[
            "chroma-mcp",
            "--client-type",
            "persistent",
            "--data-dir",
            "/Users/gavin/.chroma",
        ],
    ),
]


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
            mcp_servers=servers,
        )
    return session.agents[model]


async def process_request(model: str, message: str, tool_callback: callable = None):
    agent = get_or_create_agent(model)
    mh = session.messages.copy()
    async with agent.iter(message, message_history=mh) as agent_run:
        async for node in agent_run:
            await _process_node(node, tool_callback)
        return agent_run
