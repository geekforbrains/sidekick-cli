from pydantic_ai import Tool

from sidekick.tools.git import git_add, git_commit
from sidekick.tools.list import list_directory
from sidekick.tools.read_file import read_file
from sidekick.tools.run_command import run_command
from sidekick.tools.search import search_content, search_dirs, search_files
from sidekick.tools.update_file import update_file
from sidekick.tools.write_file import write_file


def create_tools():
    """Create Tool instances for all tools."""
    return [
        Tool(read_file),
        Tool(write_file),
        Tool(update_file),
        Tool(run_command),
        Tool(git_add),
        Tool(git_commit),
        Tool(search_files),
        Tool(search_dirs),
        Tool(search_content),
        Tool(list_directory),
    ]
