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
        print(f"[LIFECYCLE] Creating new agent for model: {session.current_model}")
        base_agent = Agent(
            model=session.current_model,
            system_prompt=_get_prompt("system"),
            tools=TOOLS,
            mcp_servers=get_configured_servers(),
        )
        session.agents[session.current_model] = ResilientAgent(base_agent)
        print(f"[LIFECYCLE] Agent created and cached for model: {session.current_model}")
    else:
        print(f"[LIFECYCLE] Reusing existing agent for model: {session.current_model}")
    return session.agents[session.current_model]


async def process_request(message: str):
    """Process a user request with the agent."""
    import asyncio
    
    # Check if we're already cancelled
    current_task = asyncio.current_task()
    print(f"[DEBUG] process_request started, task: {current_task}, cancelled: {current_task.cancelled() if current_task else 'N/A'}")
    print(f"[DEBUG] session.sigint_received: {session.sigint_received}")
    
    # If task is already cancelled on entry, something is wrong
    if current_task and current_task.cancelled():
        print("[DEBUG] WARNING: Task was already cancelled on entry!")
        import traceback
        traceback.print_stack()
    
    resilient_agent = get_or_create_agent()
    agent = resilient_agent.agent
    
    # Check MCP server status
    print(f"[DEBUG] Agent MCP servers: {len(agent._mcp_servers)} servers")
    for i, server in enumerate(agent._mcp_servers):
        print(f"[DEBUG] MCP server {i}: {server}, is_running: {getattr(server, 'is_running', 'unknown')}")
    
    mh = session.messages.copy()
    
    try:
        print("[DEBUG] About to call agent.iter()")
        async with agent.iter(message, message_history=mh) as agent_run:
            print("[DEBUG] agent.iter() context entered successfully")
            async for node in agent_run:
                print(f"[DEBUG] Processing node: {type(node).__name__}")
                # Check cancellation status during iteration
                if current_task and current_task.cancelled():
                    print("[DEBUG] Task cancelled during iteration")
                    raise asyncio.CancelledError()
                await _process_node(node)
            print("[DEBUG] All nodes processed, getting result")
            return agent_run.result.output
    except asyncio.CancelledError:
        print(f"[DEBUG] CancelledError in process_request, sigint_received: {session.sigint_received}")
        if not session.sigint_received:
            print("[DEBUG] ERROR: Task cancelled but no SIGINT received!")
            import traceback
            traceback.print_exc()
        raise
    except Exception as e:
        print(f"[DEBUG] Unexpected error in process_request: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise
