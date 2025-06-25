import asyncio
import subprocess

from pydantic_ai import RunContext

from sidekick.deps import ToolDeps
from sidekick.session import session
from sidekick.utils.command_parser import extract_commands, is_command_allowed


async def run_command(ctx: RunContext[ToolDeps], command: str) -> str:
    """Run a shell command and return its output."""
    if ctx.deps and ctx.deps.confirm_action:
        if not is_command_allowed(command, session.allowed_commands):
            panel_content = f"Command: {command}"
            if not await ctx.deps.confirm_action("Run Command", panel_content):
                raise asyncio.CancelledError("Tool execution cancelled by user")

            commands = extract_commands(command)
            session.allowed_commands.update(commands)

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    return output if output else "(no output)"
