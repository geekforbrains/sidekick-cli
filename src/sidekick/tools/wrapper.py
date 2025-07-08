from pydantic_ai import Tool

from sidekick.tools.find import find
from sidekick.tools.git import git_add, git_commit
from sidekick.tools.list import list_directory
from sidekick.tools.read_file import read_file
from sidekick.tools.run_command import run_command
from sidekick.tools.update_file import update_file
from sidekick.tools.write_file import write_file

TOOL_RETRY_LIMIT = 10


def create_tools():
    """Create Tool instances for all tools."""
    tools = [
        read_file,
        write_file,
        update_file,
        run_command,
        git_add,
        git_commit,
        find,
        list_directory,
    ]

    return [Tool(tool, max_retries=TOOL_RETRY_LIMIT) for tool in tools]
