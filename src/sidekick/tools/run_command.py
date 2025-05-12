import subprocess

from sidekick import ui


async def run_command(command: str) -> str:
    """
    Run a shell command and return the output. User must confirm risky commands.

    Args:
        command (str): The command to run.

    Returns:
        str: The output of the command (stdout and stderr) or an error message.
    """
    try:
        await ui.info(f"Shell({command})")

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        output = stdout.strip() or "No output."
        error = stderr.strip() or "No errors."
        resp = f"STDOUT:\n{output}\n\nSTDERR:\n{error}".strip()

        # Raise retry if the output is too long to prevent issues
        # Reduced limit as it's often better to be concise
        if len(resp) > 5000:
            # _msg("warning", "Command output too long, returning truncated.")
            # Include both the beginning and end of the output
            start_part = resp[:2500]
            end_part = resp[-1000:] if len(resp) > 3500 else resp[2500:]
            truncated_resp = start_part + "\n...\n[truncated]\n...\n" + end_part
            return truncated_resp

        return resp
    except FileNotFoundError as e:
        err_msg = f"Error: Command not found or failed to execute: {command}. Details: {e}"
        # _msg("error", err_msg)
        return err_msg
    # except Exception as e:
    #     err_msg = f"Error running command '{command}': {e}"
    #     _msg("error", err_msg)
    #     return err_msg
