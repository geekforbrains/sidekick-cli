import subprocess

from sidekick.utils.errors import handle_tool_errors


@handle_tool_errors
async def run_command(command: str) -> str:
    """Run a shell command and return its output."""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    return output if output else "(no output)"
