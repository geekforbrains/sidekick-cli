"""
Simplified tools for file operations and command execution.
"""

import os
import subprocess
from pathlib import Path

from sidekick.ui import error, info, success


async def read_file(filepath: str) -> str:
    """Read the contents of a file."""
    try:
        await info(f"Reading {filepath}")

        # Check file size limit (100KB)
        if os.path.getsize(filepath) > 100 * 1024:
            err_msg = f"File {filepath} is too large (max 100KB)"
            await error(err_msg)
            return err_msg

        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            await success(f"Read {len(content)} characters")
            return content

    except FileNotFoundError:
        err_msg = f"File not found: {filepath}"
        await error(err_msg)
        return err_msg
    except Exception as e:
        err_msg = f"Error reading file: {str(e)}"
        await error(err_msg)
        return err_msg


async def write_file(filepath: str, content: str) -> str:
    """Write content to a file."""
    try:
        await info(f"Writing to {filepath}")

        # Create directory if needed
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)

        await success(f"Wrote {len(content)} characters")
        return f"Successfully wrote to {filepath}"

    except Exception as e:
        err_msg = f"Error writing file: {str(e)}"
        await error(err_msg)
        return err_msg


async def update_file(filepath: str, old_content: str, new_content: str) -> str:
    """Update specific content in a file."""
    try:
        await info(f"Updating {filepath}")

        # Read current content
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()

        # Check if old content exists
        if old_content not in content:
            err_msg = "Content to replace not found in file"
            await error(err_msg)
            return err_msg

        # Replace content
        updated_content = content.replace(old_content, new_content, 1)

        # Write back
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(updated_content)

        await success("File updated successfully")
        return f"Successfully updated {filepath}"

    except FileNotFoundError:
        err_msg = f"File not found: {filepath}"
        await error(err_msg)
        return err_msg
    except Exception as e:
        err_msg = f"Error updating file: {str(e)}"
        await error(err_msg)
        return err_msg


async def run_command(command: str) -> str:
    """Run a shell command and return its output."""
    try:
        await info(f"Running: {command}")

        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)

        output = result.stdout + result.stderr

        # Truncate long output
        if len(output) > 5000:
            output = output[:2500] + "\n... (truncated) ...\n" + output[-1000:]

        if result.returncode == 0:
            await success("Command completed successfully")
        else:
            await error(f"Command failed with exit code {result.returncode}")

        return output if output else "(no output)"

    except subprocess.TimeoutExpired:
        err_msg = "Command timed out after 30 seconds"
        await error(err_msg)
        return err_msg
    except Exception as e:
        err_msg = f"Error running command: {str(e)}"
        await error(err_msg)
        return err_msg


# Tool registry for agent
TOOLS = [read_file, write_file, update_file, run_command]
