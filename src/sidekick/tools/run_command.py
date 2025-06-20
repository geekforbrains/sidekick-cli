import subprocess

from sidekick import ui


async def run_command(command: str) -> str:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        return output if output else "(no output)"
    except subprocess.TimeoutExpired:
        err_msg = "Command timed out after 30 seconds"
        ui.error(err_msg)
        return err_msg
    except Exception as e:
        err_msg = f"Error running command: {str(e)}"
        ui.error(err_msg)
        return err_msg
