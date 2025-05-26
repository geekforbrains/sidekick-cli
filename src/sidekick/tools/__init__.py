"""Sidekick tools for file operations and command execution."""

from sidekick.tools.read_file import read_file
from sidekick.tools.run_command import run_command
from sidekick.tools.update_file import update_file
from sidekick.tools.write_file import write_file

# Standard tool registry for simplified registration
TOOLS = [read_file, run_command, update_file, write_file]

__all__ = ["read_file", "run_command", "update_file", "write_file", "TOOLS"]
