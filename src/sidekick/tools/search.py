import asyncio
import shutil

# Common directories to exclude from searches to keep results focused.
# 'rg' is smart enough to handle most of these automatically via .gitignore.
EXCLUDE_DIRS = [".git", "node_modules", "__pycache__", "venv", ".venv", "env"]


async def _run_search_command(command: list) -> str:
    """Helper function to run a search command and return its output."""
    try:
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0 and stderr:
            decoded_stderr = stderr.decode().strip()
            # Suppress grep's "not found" message (exit code 1) from being a user-facing error.
            is_grep_not_found = (
                "grep" in command[0] and process.returncode == 1 and not decoded_stderr
            )
            if not is_grep_not_found:
                return f"Error executing search command:\n{decoded_stderr}"

        output = stdout.decode().strip()
        if not output:
            return "No results found."
        return output
    except FileNotFoundError:
        return f"Error: Command '{command[0]}' not found. Is it installed and in your PATH?"
    except Exception as e:
        return f"An error occurred: {str(e)}"


def _build_find_command(search_type: str, pattern: str) -> list:
    """Constructs an intelligent `find` command with exclusions."""
    command = ["find", "."]

    # Build the prune expression: \( -path './dir1' -o -path './dir2' \) -prune
    prune_paths = []
    for d in EXCLUDE_DIRS:
        prune_paths.extend(["-o", "-path", f"./{d}"])

    # The first '-o' is not needed, so we remove it.
    if prune_paths:
        prune_paths.pop(0)
        # Wrap the path expressions in parentheses for correct precedence.
        command.append("(")
        command.extend(prune_paths)
        command.append(")")
        command.extend(["-prune", "-o"])

    # Add the primary search expression.
    if search_type == "file":
        command.extend(["-type", "f", "-name", pattern])
    elif search_type == "dir":
        command.extend(["-type", "d", "-name", pattern])

    command.append("-print")
    return command


async def search_files(pattern: str) -> str:
    """
    Search for files by name or pattern (e.g., '*.py'), ignoring common non-project directories.
    """
    command = _build_find_command("file", pattern)
    return await _run_search_command(command)


async def search_dirs(pattern: str) -> str:
    """
    Search for directories by name or pattern (e.g., 'src'), ignoring common non-project directories.
    """
    command = _build_find_command("dir", pattern)
    return await _run_search_command(command)


async def search_content(text_pattern: str) -> str:
    """
    Search for a text pattern inside files. Uses 'rg' for speed and .gitignore awareness,
    otherwise falls back to an intelligent 'grep'.
    """
    if shutil.which("rg"):
        # rg is fast and respects .gitignore automatically. -n for line numbers.
        command = ["rg", "-n", "--", text_pattern, "."]
    else:
        # Fallback to recursive grep with exclusions.
        command = ["grep", "-r", "-n", "-I"]
        for d in EXCLUDE_DIRS:
            command.append(f"--exclude-dir={d}")
        command.extend([text_pattern, "."])

    return await _run_search_command(command)
