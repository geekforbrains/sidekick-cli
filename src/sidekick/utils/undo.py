import subprocess
import time
from pathlib import Path

from pydantic_ai.messages import ModelResponse, TextPart

from .. import session
from . import ui
from .system import get_session_dir


def init_undo_system():
    """
    Initialize the undo system by creating a Git repository
    in the ~/.sidekick/sessions/<session-id> directory.

    Only initializes if current directory is in a git repository and not the home directory.

    Returns:
        bool: True if the undo system was initialized, False otherwise.
    """
    # Get current working directory and home directory
    cwd = Path.cwd()
    home_dir = Path.home()

    # Skip if we're in the home directory or its immediate subdirectories
    if cwd == home_dir:
        ui.warning("Undo system disabled, running from home directory")
        return False

    # Skip if we're in a subdirectory of the home directory that doesn't look like a project
    # This helps avoid running in places like ~/Downloads, ~/Documents, etc.
    if cwd.parent == home_dir and not (cwd / ".git").exists():
        ui.warning("Undo system disabled, running from home subdirectory")
        return False

    # Check if current directory is in a git repository
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(cwd),
            capture_output=True,
            timeout=2,
            text=True,
        )

        if result.returncode != 0 or "true" not in result.stdout.lower():
            ui.warning("Undo system disabled: Current directory is not in a git repository")
            return False

    except subprocess.TimeoutExpired:
        ui.warning("Undo system disabled, git command timed out")
        return False
    except FileNotFoundError:
        ui.warning("Undo system disabled, git command not found")
        return False
    except Exception as e:
        ui.warning(f"Undo system disabled: {str(e)}")
        return False

    # Get the session directory path
    session_dir = get_session_dir()
    sidekick_git_dir = session_dir / ".git"

    # Check if already initialized
    if sidekick_git_dir.exists():
        return True

    # Initialize Git repository for undo system
    try:
        # Initialize a new git repository in the session directory
        subprocess.run(
            ["git", "init", str(session_dir)], capture_output=True, check=True, timeout=5
        )

        # Set up git parameters for this repo
        git_dir_arg = f"--git-dir={sidekick_git_dir}"
        work_tree_arg = f"--work-tree={session_dir}"

        # Configure git identity for this repository
        subprocess.run(
            ["git", git_dir_arg, work_tree_arg, "config", "user.name", "Sidekick CLI"],
            capture_output=True,
            timeout=3,
        )
        subprocess.run(
            ["git", git_dir_arg, work_tree_arg, "config", "user.email", "sidekick@example.com"],
            capture_output=True,
            timeout=3,
        )

        # Create a placeholder file to ensure there's something to commit
        placeholder = session_dir / ".sidekick-undo"
        placeholder.write_text("Sidekick undo system tracking file")

        # Add the placeholder file
        subprocess.run(
            ["git", git_dir_arg, work_tree_arg, "add", ".sidekick-undo"],
            capture_output=True,
            check=True,
            timeout=5,
        )

        # Create initial commit with just the placeholder
        subprocess.run(
            [
                "git",
                git_dir_arg,
                work_tree_arg,
                "commit",
                "-m",
                "Initial commit for sidekick undo history",
            ],
            capture_output=True,
            check=True,
            timeout=5,
        )

        return True
    except subprocess.TimeoutExpired:
        ui.warning("Undo system initialization timed out")
        return False
    except Exception as e:
        ui.warning(f"Undo system initialization failed: {str(e)}")
        return False


def commit_for_undo(message_prefix="sidekick"):
    """
    Commit the current state to the undo repository.

    Args:
        message_prefix (str): Prefix for the commit message.

    Returns:
        bool: True if the commit was successful, False otherwise.
    """
    from . import ui

    # Get the session directory and git dir
    session_dir = get_session_dir()
    sidekick_git_dir = session_dir / ".git"

    if not sidekick_git_dir.exists():
        return False

    try:
        git_dir_arg = f"--git-dir={sidekick_git_dir}"
        work_tree_arg = f"--work-tree={session_dir}"

        # Add all files
        subprocess.run(
            ["git", git_dir_arg, work_tree_arg, "add", "."], capture_output=True, timeout=5
        )

        # Create commit with timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"{message_prefix} - {timestamp}"

        result = subprocess.run(
            ["git", git_dir_arg, work_tree_arg, "commit", "-m", commit_message],
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
        ui.warning(f"Undo system commit failed: {str(e)}")
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
        work_tree_arg = f"--work-tree={session_dir}"

        # Get commit log to check if we have commits to undo
        result = subprocess.run(
            ["git", git_dir_arg, work_tree_arg, "log", "--format=%H", "-n", "2"],
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
            ["git", git_dir_arg, work_tree_arg, "log", "--format=%B", "-n", "1"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        commit_msg = commit_msg_result.stdout.strip()

        # Perform reset to previous commit
        subprocess.run(
            ["git", git_dir_arg, work_tree_arg, "reset", "--hard", "HEAD~1"],
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
