"""
Module: sidekick.tools.run_command

Command execution tool for agent operations in the Sidekick application.
Provides controlled shell command execution with output capture and truncation.
"""

import subprocess

from sidekick.constants import (CMD_OUTPUT_FORMAT, CMD_OUTPUT_NO_ERRORS, CMD_OUTPUT_NO_OUTPUT,
                                CMD_OUTPUT_TRUNCATED, COMMAND_OUTPUT_END_SIZE,
                                COMMAND_OUTPUT_START_INDEX, COMMAND_OUTPUT_THRESHOLD,
                                ERROR_COMMAND_EXECUTION, MAX_COMMAND_OUTPUT)
from sidekick.types import ToolResult
from sidekick.ui.output import info
from sidekick.ui.panels import error


async def run_command(command: str) -> ToolResult:
    """
    Run a shell command and return the output. User must confirm risky commands.

    Args:
        command (str): The command to run.

    Returns:
        ToolResult: The output of the command (stdout and stderr) or an error message.
    """
    try:
        await info(f"Shell({repr(command)})")

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        output = stdout.strip() or CMD_OUTPUT_NO_OUTPUT
        stderr_output = stderr.strip() or CMD_OUTPUT_NO_ERRORS
        resp = CMD_OUTPUT_FORMAT.format(output=output, error=stderr_output).strip()

        if len(resp) > MAX_COMMAND_OUTPUT:
            start_part = resp[:COMMAND_OUTPUT_START_INDEX]
            end_part = (
                resp[-COMMAND_OUTPUT_END_SIZE:]
                if len(resp) > COMMAND_OUTPUT_THRESHOLD
                else resp[COMMAND_OUTPUT_START_INDEX:]
            )
            truncated_resp = start_part + CMD_OUTPUT_TRUNCATED + end_part
            return truncated_resp

        return resp

    except FileNotFoundError as file_error:
        err_msg = ERROR_COMMAND_EXECUTION.format(command=command, error=file_error)
        await error(err_msg)
        return err_msg
    except Exception as exec_error:
        err_msg = f"Error running command '{command}': {exec_error}"
        await error(err_msg)
        return err_msg
