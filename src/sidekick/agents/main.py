from datetime import datetime, timezone

from pydantic_ai import Agent, Tool
from pydantic_ai.messages import ModelRequest, ToolReturnPart

from sidekick.core.state import StateManager
from sidekick.tools.read_file import read_file
from sidekick.tools.run_command import run_command
from sidekick.tools.update_file import update_file
from sidekick.tools.write_file import write_file
from sidekick.utils.mcp import get_mcp_servers


async def _process_node(node, tool_callback, state_manager: StateManager):
    if hasattr(node, "request"):
        state_manager.session.messages.append(node.request)

    if hasattr(node, "model_response"):
        state_manager.session.messages.append(node.model_response)
        for part in node.model_response.parts:
            if part.part_kind == "tool-call" and tool_callback:
                await tool_callback(part, node)


def get_or_create_agent(model, state_manager: StateManager):
    if model not in state_manager.session.agents:
        max_retries = state_manager.session.user_config["settings"]["max_retries"]
        state_manager.session.agents[model] = Agent(
            model=model,
            tools=[
                Tool(read_file, max_retries=max_retries),
                Tool(run_command, max_retries=max_retries),
                Tool(update_file, max_retries=max_retries),
                Tool(write_file, max_retries=max_retries),
            ],
            mcp_servers=get_mcp_servers(),
        )
    return state_manager.session.agents[model]


def patch_tool_messages(error_message="Tool operation failed", state_manager: StateManager = None):
    """
    Find any tool calls without responses and add synthetic error responses for them.
    Takes an error message to use in the synthesized tool response.

    Ignores tools that have corresponding retry prompts as the model is already
    addressing them.
    """
    # For backward compatibility, import session if state_manager is not provided
    if state_manager is None:
        from sidekick import session
        messages = session.messages
    else:
        messages = state_manager.session.messages
        
    if not messages:
        return

    # Map tool calls to their tool returns
    tool_calls = {}  # tool_call_id -> tool_name
    tool_returns = set()  # set of tool_call_ids with returns
    retry_prompts = set()  # set of tool_call_ids with retry prompts

    for message in messages:
        if hasattr(message, "parts"):
            for part in message.parts:
                if (
                    hasattr(part, "part_kind")
                    and hasattr(part, "tool_call_id")
                    and part.tool_call_id
                ):
                    if part.part_kind == "tool-call":
                        tool_calls[part.tool_call_id] = part.tool_name
                    elif part.part_kind == "tool-return":
                        tool_returns.add(part.tool_call_id)
                    elif part.part_kind == "retry-prompt":
                        retry_prompts.add(part.tool_call_id)

    # Identify orphaned tools (those without responses and not being retried)
    for tool_call_id, tool_name in list(tool_calls.items()):
        if tool_call_id not in tool_returns and tool_call_id not in retry_prompts:
            messages.append(
                ModelRequest(
                    parts=[
                        ToolReturnPart(
                            tool_name=tool_name,
                            content=error_message,
                            tool_call_id=tool_call_id,
                            timestamp=datetime.now(timezone.utc),
                            part_kind="tool-return",
                        )
                    ],
                    kind="request",
                )
            )


async def process_request(model: str, message: str, state_manager: StateManager, tool_callback: callable = None):
    agent = get_or_create_agent(model, state_manager)
    mh = state_manager.session.messages.copy()
    async with agent.iter(message, message_history=mh) as agent_run:
        async for node in agent_run:
            await _process_node(node, tool_callback, state_manager)
        return agent_run
