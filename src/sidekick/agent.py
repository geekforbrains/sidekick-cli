import asyncio
from pathlib import Path
from typing import Optional, Any

from pydantic_ai import Agent

from sidekick import ui
from sidekick.constants import MODELS
from sidekick.deps import ToolDeps
from sidekick.mcp import MCPAgent, load_mcp_servers
from sidekick.session import session
from sidekick.tools import TOOLS


def _get_prompt(name: str) -> str:
    try:
        prompt_path = Path(__file__).parent / "prompts" / f"{name}.txt"
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return f"Error: Prompt file '{name}.txt' not found"


async def _track_tool_request(part):
    if not hasattr(session, "pending_tools"):
        session.pending_tools = {}

    session.pending_tools[part.tool_call_id] = {"name": part.tool_name, "args": part.args_as_dict()}


async def _cleanup_pending_tools():
    if hasattr(session, "pending_tools"):
        session.pending_tools.clear()


async def _process_node(node):
    if hasattr(node, "request"):
        session.messages.append(node.request)

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

            elif part.part_kind == "tool-return" and hasattr(session, "pending_tools"):
                tool_id = getattr(part, "tool_call_id", None)
                if tool_id and tool_id in session.pending_tools:
                    tool_info = session.pending_tools[tool_id]

                    tool_name = tool_info["name"]
                    if tool_name not in session.tool_usage:
                        session.tool_usage[tool_name] = 0
                    session.tool_usage[tool_name] += 1

                    del session.pending_tools[tool_id]

    if hasattr(node, "model_response"):
        session.messages.append(node.model_response)

        tool_calls = [part for part in node.model_response.parts if part.part_kind == "tool-call"]
        for tool_call in tool_calls:
            await _track_tool_request(tool_call)


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

        options_content = [
            "Options:",
            "  y - Yes, execute this tool",
            "  a - Always allow this tool",
            "  n - No, cancel this execution",
        ]
        ui.display_confirmation_panel("\n".join(options_content))

        while True:
            choice = (
                ui.console.input(
                    f"  [{ui.colors.warning}]Continue?[/{ui.colors.warning}] [y/a/n] (default: y): "
                )
                .lower()
                .strip()
            )

            if choice == "" or choice in ["y", "yes"]:
                ui.console.print()
                if session.spinner:
                    session.spinner.start()
                return True
            elif choice in ["a", "always"]:
                session.disabled_confirmations.add(tool_name)
                ui.console.print()
                if session.spinner:
                    session.spinner.start()
                return True
            elif choice in ["n", "no"]:
                ui.console.print()
                return False
            else:
                ui.console.print(
                    "  Invalid choice. Please enter y, a, or n.", style=ui.colors.error
                )

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


async def process_request(message: str):
    mcp_agent = get_or_create_agent()
    agent = mcp_agent.agent

    mh = session.messages.copy()

    deps = ToolDeps(
        confirm_action=_create_confirmation_callback(),
        display_tool_status=_create_display_tool_status_callback()
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

            return agent_run.result.output
    except asyncio.CancelledError as e:
        if str(e) == "Tool execution cancelled by user":
            ui.warning("Tool execution cancelled")
            return None
        raise
    finally:
        await _cleanup_pending_tools()
