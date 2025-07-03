import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from pydantic_ai import Agent, CallToolsNode
from pydantic_ai.messages import (
    ModelRequest,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    TextPart,
)

from sidekick import ui
from sidekick.constants import MODELS
from sidekick.deps import ToolDeps
from sidekick.mcp import MCPAgent, load_mcp_servers
from sidekick.session import session
from sidekick.tools import TOOLS
from sidekick.utils.guide import get_guide

log = logging.getLogger(__name__)


def _get_prompt(name: str) -> str:
    try:
        prompt_path = Path(__file__).parent / "prompts" / f"{name}.txt"
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return f"Error: Prompt file '{name}.txt' not found"


async def _process_node(node):
    # from rich import print
    # print('-' * 20)
    # print(node)
    # print('-' * 20)

    if isinstance(node, CallToolsNode):
        for part in node.model_response.parts:
            if isinstance(part, ToolCallPart):
                log.debug(f"Calling tool: {part.tool_name}")

            # I cant' find a definitive way to check if a text part is a "thinking" response
            # or not, but majority of the time they are accompanied by other tool calls.
            # Using that as a basis for showing "thinking" messages.
            if isinstance(part, TextPart) and len(node.model_response.parts) > 1:
                ui.stop_spinner()
                ui.thinking(part.content)
                ui.start_spinner()

    if hasattr(node, "request"):
        session.messages.append(node.request)
        log.debug("Added request to message history")

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

    if hasattr(node, "model_response"):
        session.messages.append(node.model_response)
        log.debug("Added model response to message history")


def _calculate_usage_costs(usage):
    cached_tokens = 0
    if hasattr(usage, "details") and usage.details:
        for detail in usage.details:
            if hasattr(detail, "cached_tokens"):
                cached_tokens += detail.cached_tokens

    input_tokens = usage.request_tokens
    non_cached_input = input_tokens - cached_tokens
    output_tokens = usage.response_tokens

    model_ids = list(MODELS.keys())
    pricing = MODELS.get(session.current_model, MODELS[model_ids[0]])["pricing"]

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
    async def confirm(title: str, preview: Any, footer: Optional[str] = None) -> bool:
        tool_name = title.split(":")[0].strip() if ":" in title else title

        if not session.confirmation_enabled or tool_name in session.disabled_confirmations:
            return True

        if session.spinner:
            session.spinner.stop()

        ui.display_tool_panel(preview, title, footer)

        # Display confirmation options without using a panel, but still
        # indented by two spaces so they line up with other panel content.
        options = (
            ("y", "Yes, execute this tool"),
            ("a", "Always allow this tool"),
            ("n", "No, cancel this execution"),
        )

        # Add a single blank line before options
        ui.console.print()

        for key, description in options:
            ui.console.print(f"  {key}: {description}", style=ui.colors.warning)

        while True:
            choice = ui.console.input("  Continue? (y): ").lower().strip()

            if choice == "" or choice in ["y", "yes"]:
                ui.line()
                ui.reset_output_context()  # Reset after user input
                if session.spinner:
                    session.spinner.start()
                return True
            elif choice in ["a", "always"]:
                session.disabled_confirmations.add(tool_name)
                ui.line()
                ui.reset_output_context()  # Reset after user input
                if session.spinner:
                    session.spinner.start()
                return True
            elif choice in ["n", "no"]:
                ui.reset_output_context()  # Reset after user input
                return False

    return confirm


def _create_display_tool_status_callback():
    async def display(title: str, *args: Any, **kwargs: Any) -> None:
        """
        Display the current tool status.

        Args:
            title: str
            *args: Any
            **kwargs: Any
                Keyword arguments passed to the tool. These will be rendered in the
                form ``key=value`` in the output.
        """
        if session.spinner:
            session.spinner.stop()

        parts = []
        if args:
            parts.extend(str(arg) for arg in args)
        if kwargs:
            parts.extend(f"{k}={v}" for k, v in kwargs.items())

        arg_str = ", ".join(parts)
        ui.info(f"{title}({arg_str})")

        if session.spinner:
            session.spinner.start()

    return display


def _patch_history_on_error(error_message: str):
    """
    Patches the message history with a ToolReturnPart on error.
    """
    if not session.messages:
        return

    last_message = session.messages[-1]

    if not (
        hasattr(last_message, "kind")
        and last_message.kind == "response"
        and hasattr(last_message, "parts")
    ):
        return

    last_tool_call = None
    for part in reversed(last_message.parts):
        if hasattr(part, "part_kind") and part.part_kind == "tool-call":
            last_tool_call = part
            break

    if last_tool_call:
        tool_return = ToolReturnPart(
            tool_name=last_tool_call.tool_name,
            tool_call_id=last_tool_call.tool_call_id,
            content=error_message,
        )
        session.messages.append(ModelRequest(parts=[tool_return]))


async def process_request(message: str):
    log.debug(f"Processing request: {message.replace('\n', ' ')[:100]}...")

    mcp_agent = get_or_create_agent()
    agent = mcp_agent.agent

    mh = session.messages.copy()
    log.debug(f"Message history size: {len(mh)}")

    project_guide = get_guide(session)
    if project_guide:
        guide_message = ModelRequest(parts=[UserPromptPart(content=project_guide)])
        mh.insert(0, guide_message)
        log.debug("Prepended project guide to message history")

    deps = ToolDeps(
        confirm_action=_create_confirmation_callback(),
        display_tool_status=_create_display_tool_status_callback(),
    )

    try:
        async with agent.iter(message, deps=deps, message_history=mh) as agent_run:
            async for node in agent_run:
                await _process_node(node)

            usage = agent_run.usage()
            if usage:
                session.last_usage = _calculate_usage_costs(usage)
                session.total_tokens += usage.total_tokens
                session.total_cost = session.last_usage["total_cost"]

            result = agent_run.result.output
            log.debug(f"Agent response: {result.replace('\n', ' ')[:100]}...")
            return result
    except asyncio.CancelledError as e:
        log.debug(f"Request cancelled: {e}")
        _patch_history_on_error(str(e))
        ui.line()
        ui.warning("Tool execution cancelled")
        return None
    except Exception as e:
        log.error(f"Error processing request: {e}", exc_info=True)
        _patch_history_on_error(f"Tool execution failed: {e}")
        ui.warning(f"An error occurred: {e}")
        return None
