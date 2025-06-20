from .read_file import read_file
from .run_command import run_command
from .update_file import update_file
from .write_file import write_file

TOOLS = [
    read_file,
    write_file,
    update_file,
    run_command,
]

TOOL_DISPLAY_NAMES = {
    "read_file": "Read",
    "write_file": "Write",
    "update_file": "Update",
    "run_command": "Run",
}
