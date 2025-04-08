import subprocess
import time
from pathlib import Path

from pydantic_ai.messages import ModelResponse, TextPart

from .. import session
from . import ui
from .system import get_session_dir


def is_in_git_project(directory=None):
    """
    Recursively check if the given directory is inside a git project.

    Args:
        directory (Path, optional): Directory to check. Defaults to current working directory.

    Returns:
        bool: True if in a git project, False otherwise
    """
    if directory is None:
        directory = Path.cwd()

    if (directory / ".git").exists():
        return True

    if directory == directory.parent:
        return False

    return is_in_git_project(directory.parent)


def init_undo_system():
    """
    Initialize the undo system by creating a Git repository
    in the ~/.sidekick/sessions/<session-id> directory.

    Skip initialization if running from home directory or not in a git project.

    Returns:
        bool: True if the undo system was initialized, False otherwise.
    """
    cwd = Path.cwd()
    home_dir = Path.home()

    if cwd == home_dir:
        ui.warning("Undo system disabled, running from home directory")
        return False

    if not is_in_git_project():
        ui.warning("Undo system disable, not in a git project")
        return False

    # Get the session directory path
    session_dir = get_session_dir()
    sidekick_git_dir = session_dir / ".git"

    # Check if already initialized
    if sidekick_git_dir.exists():
        return True

    # Initialize Git repository
    try:
        subprocess.run(
            ["git", "init", str(session_dir)], capture_output=True, check=True, timeout=5
        )

        # Make an initial commit
        git_dir_arg = f"--git-dir={sidekick_git_dir}"

        # Add all files
        subprocess.run(["git", git_dir_arg, "add", "."], capture_output=True, check=True, timeout=5)

        # Create initial commit
        subprocess.run(
            ["git", git_dir_arg, "commit", "-m", "Initial commit for sidekick undo history"],
            capture_output=True,
            check=True,
            timeout=5,
        )

        return True
    except subprocess.TimeoutExpired:
        ui.warning("Undo system initialization timed out")
        return False
    except Exception as e:
        ui.warning(f"Error initializing undo system: {e}")
        return False


def commit_for_undo(message_prefix="sidekick"):
    """
    Commit the current state to the undo repository.

    Args:
        message_prefix (str): Prefix for the commit message.

    Returns:
        bool: True if the commit was successful, False otherwise.
    """
    # Get the session directory and git dir
    session_dir = get_session_dir()
    sidekick_git_dir = session_dir / ".git"

    if not sidekick_git_dir.exists():
        return False

    try:
        git_dir_arg = f"--git-dir={sidekick_git_dir}"

        # Add all files
        subprocess.run(["git", git_dir_arg, "add", "."], capture_output=True, timeout=5)

        # Create commit with timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"{message_prefix} - {timestamp}"

        result = subprocess.run(
            ["git", git_dir_arg, "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Handle case where there are no changes to commit
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            return False

        return True
    except subprocess.TimeoutExpired:
        ui.warning("Undo system commit timed out")
        return False
    except Exception as e:
        ui.warning(f"Error creating undo commit: {e}")
        return False


def perform_undo():
    """
    Undo the most recent change by resetting to the previous commit.
    Also adds a system message to the chat history to inform the AI
    that the last changes were undone.

    Returns:
        tuple: (bool, str) - Success status and message
    """
    # Get the session directory and git dir
    session_dir = get_session_dir()
    sidekick_git_dir = session_dir / ".git"

    if not sidekick_git_dir.exists():
        return False, "Undo system not initialized"

    try:
        git_dir_arg = f"--git-dir={sidekick_git_dir}"

        # Get commit log to check if we have commits to undo
        result = subprocess.run(
            ["git", git_dir_arg, "log", "--format=%H", "-n", "2"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )

        commits = result.stdout.strip().split("\n")
        if len(commits) < 2:
            return False, "Nothing to undo"

        # Get the commit message of the commit we're undoing for context
        commit_msg_result = subprocess.run(
            ["git", git_dir_arg, "log", "--format=%B", "-n", "1"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        commit_msg = commit_msg_result.stdout.strip()

        # Perform reset to previous commit
        subprocess.run(
            ["git", git_dir_arg, "reset", "--hard", "HEAD~1"],
            capture_output=True,
            check=True,
            timeout=5,
        )

        # Add a system message to the chat history to inform the AI
        # about the undo operation
        session.messages.append(
            ModelResponse(
                parts=[
                    TextPart(
                        content=(
                            "The last changes were undone. "
                            f"Commit message of undone changes: {commit_msg}"
                        )
                    )
                ],
                kind="response",
            )
        )

        return True, "Successfully undid last change"
    except subprocess.TimeoutExpired:
        return False, "Undo operation timed out"
    except Exception as e:
        return False, f"Error performing undo: {e}"
