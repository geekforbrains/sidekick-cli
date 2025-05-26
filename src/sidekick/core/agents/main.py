"""Module: sidekick.core.agents.main

Main agent functionality and coordination for the Sidekick CLI.
Provides agent creation, message processing, and tool call management.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ToolReturnPart

from sidekick.core.tool_handler import create_tools_with_config
from sidekick.services.mcp import get_mcp_servers
from sidekick.tools import TOOLS
from sidekick.types import (AgentRun, ErrorMessage, ModelName, PydanticAgent, SessionState,
                            ToolCallback, ToolCallId, ToolName)


async def _process_node(node, tool_callback: Optional[ToolCallback], session: SessionState):
    if hasattr(node, "request"):
        session.messages.append(node.request)

    if hasattr(node, "model_response"):
        session.messages.append(node.model_response)
        for part in node.model_response.parts:
            if part.part_kind == "tool-call" and tool_callback:
                await tool_callback(part, node)


def get_or_create_agent(model: ModelName, session: SessionState) -> PydanticAgent:
    if model not in session.agents:
        max_retries = session.user_config["settings"]["max_retries"]
        session.agents[model] = Agent(
            model=model,
            tools=create_tools_with_config(TOOLS, max_retries),
            mcp_servers=get_mcp_servers(session),
        )
    return session.agents[model]


def patch_tool_messages(
    error_message: ErrorMessage = "Tool operation failed",
    session: SessionState = None,
):
    """
    Find any tool calls without responses and add synthetic error responses for them.
    Takes an error message to use in the synthesized tool response.

    Ignores tools that have corresponding retry prompts as the model is already
    addressing them.
    """
    if session is None:
        raise ValueError("session is required for patch_tool_messages")

    messages = session.messages

    if not messages:
        return

    tool_calls: dict[ToolCallId, ToolName] = {}
    tool_returns: set[ToolCallId] = set()
    retry_prompts: set[ToolCallId] = set()

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


async def process_request(
    model: ModelName,
    message: str,
    session: SessionState,
    tool_callback: Optional[ToolCallback] = None,
) -> AgentRun:
    agent = get_or_create_agent(model, session)
    mh = session.messages.copy()
    async with agent.iter(message, message_history=mh) as agent_run:
        async for node in agent_run:
            await _process_node(node, tool_callback, session)
        return agent_run
