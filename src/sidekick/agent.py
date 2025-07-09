import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from pydantic_ai import Agent, CallToolsNode
from pydantic_ai.messages import (
    TextPart,
    ToolCallPart,
)

from sidekick import ui
from sidekick.deps import ToolDeps
from sidekick.mcp import MCPAgent, load_mcp_servers
from sidekick.session import session
from sidekick.tools import TOOLS
from sidekick.usage import usage_tracker
from sidekick.utils.error import ErrorContext

log = logging.getLogger(__name__)


def _get_prompt(name: str) -> str:
    try:
        prompt_path = Path(__file__).parent / "prompts" / f"{name}.txt"
        return prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return f"Error: Prompt file '{name}.txt' not found"


async def _process_node(node, message_history):
    if isinstance(node, CallToolsNode):
        for part in node.model_response.parts:
            if isinstance(part, ToolCallPart):
                log.debug(f"Calling tool: {part.tool_name}")

            # I cant' find a definitive way to check if a text part is a "thinking" response
            # or not, but majority of the time they are accompanied by other tool calls.
            # Using that as a basis for showing "thinking" messages.
            if isinstance(part, TextPart) and len(node.model_response.parts) > 1:
                ui.stop_spinner()
                ui.thinking_panel(part.content)
                ui.start_spinner()

    if hasattr(node, "request"):
        message_history.add_request(node.request)

        for part in node.request.parts:
            if part.part_kind == "retry-prompt":
                ui.stop_spinner()
                error_msg = (
                    part.content
                    if hasattr(part, "content") and isinstance(part.content, str)
                    else "Trying a different approach"
                )
                ui.muted(f"{error_msg}")
                ui.start_spinner()

    if hasattr(node, "model_response"):
        message_history.add_response(node.model_response)


def create_agent():
    """Create a fresh agent instance with MCP server support."""
    base_agent = Agent(
        model=session.current_model,
        system_prompt=_get_prompt("system"),
        tools=TOOLS,
        mcp_servers=load_mcp_servers(),
        deps_type=ToolDeps,
    )
    return MCPAgent(base_agent)


def _create_confirmation_callback():
    async def confirm(title: str, preview: Any, footer: Optional[str] = None) -> bool:
        tool_name = title.split(":")[0].strip() if ":" in title else title

        if not session.confirmation_enabled or tool_name in session.disabled_confirmations:
            return True

        ui.stop_spinner()
        ui.tool(preview, title, footer)

        # Display confirmation options without using a panel, but still
        # indented by two spaces so they line up with other panel content.
        options = (
            ("y", "Yes, execute this tool"),
            ("a", "Always allow this tool"),
            ("n", "No, cancel this execution"),
        )

        for key, description in options:
            ui.muted(f"{key}: {description}", indent=2)

        ui.line()  # Add blank line before user input prompt
        while True:
            choice = ui.console.input("  Continue? (y): ").lower().strip()

            if choice == "" or choice in ["y", "yes"]:
                ui.reset_context()  # Mark as user input for proper spacing
                ui.start_spinner()
                return True
            elif choice in ["a", "always"]:
                session.disabled_confirmations.add(tool_name)
                ui.reset_context()  # Mark as user input for proper spacing
                ui.start_spinner()
                return True
            elif choice in ["n", "no"]:
                ui.reset_context()  # Mark as user input for proper spacing
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
        ui.stop_spinner()

        parts = []
        if args:
            parts.extend(str(arg) for arg in args)
        if kwargs:
            parts.extend(f"{k}={v}" for k, v in kwargs.items())

        arg_str = ", ".join(parts)
        ui.info(f"{title}({arg_str})")
        ui.start_spinner()

    return display


async def process_request(message: str, message_history):
    log.debug(f"Processing request: {message.replace('\n', ' ')[:100]}...")

    async with create_agent() as mcp_agent:
        agent = mcp_agent.agent

        mh = message_history.get_messages_for_agent()
        log.debug(f"Message history size: {len(mh)}")

        deps = ToolDeps(
            confirm_action=_create_confirmation_callback(),
            display_tool_status=_create_display_tool_status_callback(),
        )

        ctx = ErrorContext("agent", ui)
        ctx.add_cleanup(lambda e: message_history.patch_on_error(str(e)))

        try:
            async with agent.iter(message, deps=deps, message_history=mh) as agent_run:
                async for node in agent_run:
                    await _process_node(node, message_history)

                usage = agent_run.usage()
                if usage:
                    usage_tracker.record_usage(session.current_model, usage)

                result = agent_run.result.output
                log.debug(f"Agent response: {result.replace('\n', ' ')[:100]}...")
                return result
        except asyncio.CancelledError:
            raise
        except Exception as e:
            if type(e).__name__ == "ClosedResourceError" and e.__class__.__module__ == "anyio":
                raise asyncio.CancelledError() from e
            if type(e).__name__ == "McpError" and str(e) == "Connection closed":
                raise asyncio.CancelledError() from e
            return await ctx.handle(e)
