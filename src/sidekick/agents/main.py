from pydantic_ai import Agent, Tool

from sidekick import session
from sidekick.tools.read_file import read_file
from sidekick.tools.run_command import run_command
from sidekick.tools.update_file import update_file
from sidekick.tools.write_file import write_file
from sidekick.utils.mcp import get_mcp_servers


# def _patch_tool_message(self, tool_name, tool_call_id):
#     """
#     If a tool is cancelled, we need to patch a response otherwise
#     some models will throw an error.
#
#     Example:
#         self._patch_tool_message(part.tool_name, part.tool_call_id)
#     """
#     session.messages.append(
#         ModelRequest(
#             parts=[
#                 ToolReturnPart(
#                     tool_name=tool_name,
#                     content="Operation aborted by user.",
#                     tool_call_id=tool_call_id,
#                     timestamp=datetime.now(timezone.utc),
#                     part_kind="tool-return",
#                 )
#             ],
#             kind="request",
#         )
#     )


async def _process_node(node, tool_callback):
    if hasattr(node, "request"):
        session.messages.append(node.request)

    if hasattr(node, "model_response"):
        session.messages.append(node.model_response)
        for part in node.model_response.parts:
            if part.part_kind == "tool-call" and tool_callback:
                await tool_callback(part, node)


def get_or_create_agent(model):
    if model not in session.agents:
        max_retries = session.user_config['settings']['max_retries']
        session.agents[model] = Agent(
            model=model,
            tools=[
                Tool(read_file, max_retries=max_retries),
                Tool(run_command, max_retries=max_retries),
                Tool(update_file, max_retries=max_retries),
                Tool(write_file, max_retries=max_retries),
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
