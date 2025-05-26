"""
Module: sidekick.services.undo_service

Provides Git-based undo functionality for Sidekick operations.
Manages automatic commits and rollback operations.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

from pydantic_ai.messages import ModelResponse, TextPart

from sidekick.constants import UNDO_INITIAL_COMMIT
from sidekick.exceptions import GitOperationError
from sidekick.types import SessionState
from sidekick.utils.system import get_session_dir


def is_system_directory(directory: Path) -> bool:
    """
    Check if directory is a system directory that should not have undo enabled.

    Args:
        directory: Directory path to check.

    Returns:
        bool: True if directory is a system directory, False otherwise
    """
    system_paths = {
        "/",
        "/usr",
        "/var",
        "/etc",
        "/bin",
        "/sbin",
        "/System",
        "/Library",
        "/Applications",
        "/Users",
        "/Windows",
        "/Program Files",
        "/Program Files (x86)",
    }

    system_prefixes = [
        "/usr/",
        "/var/",
        "/etc/",
        "/bin/",
        "/sbin/",
        "/System/",
        "/Library/",
        "/Applications/",
        "/Windows/",
        "/Program Files/",
    ]

    normalized_path = str(directory.absolute())

    if normalized_path in system_paths:
        return True

    for prefix in system_prefixes:
        if normalized_path.startswith(prefix):
            return True

    return False


def count_files_in_directory(directory: Path, limit: int = 5000) -> int:
    """
    Count files in directory up to the specified limit.

    Args:
        directory: Directory to scan.
        limit: Maximum number of files to count before stopping.

    Returns:
        int: Number of files found, up to limit
    """
    try:
        count = 0
        for entry in directory.iterdir():
            count += 1
            if count >= limit:
                break
        return count
    except (PermissionError, OSError, FileNotFoundError):
        return 0


def is_safe_for_undo(directory: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Check if directory is safe for undo operations.

    Args:
        directory: Directory to check. Defaults to current working directory.

    Returns:
        tuple: (is_safe, reason)
    """
    if directory is None:
        directory = Path.cwd()

    if is_system_directory(directory):
        return False, "System directory"

    if len(directory.parts) < 3:
        return False, "Too close to filesystem root"

    file_count = count_files_in_directory(directory, 5000)
    if file_count >= 5000:
        return False, "Directory contains too many files"

    return True, "Safe for undo operations"


def get_undo_status(session: SessionState) -> Tuple[bool, str]:
    """
    Get the current status of the undo system.

    Args:
        session: The SessionState instance.

    Returns:
        tuple: (bool, str) - (is_available, status_message)
    """
    cwd = Path.cwd()
    home_dir = Path.home()

    if cwd == home_dir:
        return False, "Disabled (running from home directory)"

    is_safe, reason = is_safe_for_undo()
    if not is_safe:
        return False, f"Disabled ({reason.lower()})"

    session_dir = get_session_dir(session)
    sidekick_git_dir = session_dir / ".git"

    if not sidekick_git_dir.exists():
        return False, "Not initialized"

    try:
        git_dir_arg = f"--git-dir={sidekick_git_dir}"
        result = subprocess.run(
            ["git", git_dir_arg, "log", "--format=%H", "-n", "2"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        commits = result.stdout.strip().split("\n")
        if len(commits) < 2:
            return True, "Available (no changes to undo)"
        else:
            return True, f"Available ({len(commits) - 1} commits to undo)"
    except Exception:
        return False, "Error checking status"


def init_undo_system(session: SessionState) -> bool:
    """
    Initialize the undo system by creating a Git repository
    in the ~/.sidekick/sessions/<session-id> directory.

    Args:
        session: The SessionState instance.

    Returns:
        bool: True if the undo system was initialized, False otherwise.
    """
    session_dir = get_session_dir(session)
    sidekick_git_dir = session_dir / ".git"

    if sidekick_git_dir.exists():
        return True

    # Initialize Git repository
    try:
        subprocess.run(
            ["git", "init", str(session_dir)], capture_output=True, check=True, timeout=5
        )

        # Make an initial commit
        git_dir_arg = f"--git-dir={sidekick_git_dir}"

        subprocess.run(["git", git_dir_arg, "add", "."], capture_output=True, check=True, timeout=5)

        subprocess.run(
            ["git", git_dir_arg, "commit", "-m", UNDO_INITIAL_COMMIT],
            capture_output=True,
            check=True,
            timeout=5,
        )

        return True
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def commit_for_undo(
    message_prefix: str = "sidekick", session: Optional[SessionState] = None
) -> bool:
    """
    Commit the current state to the undo repository.

    Args:
        message_prefix (str): Prefix for the commit message.
        session: The SessionState instance.

    Returns:
        bool: True if the commit was successful, False otherwise.
    """
    # Get the session directory and git dir
    if session is None:
        raise ValueError("session is required for commit_for_undo")
    session_dir = get_session_dir(session)
    sidekick_git_dir = session_dir / ".git"

    if not sidekick_git_dir.exists():
        return False

    try:
        git_dir_arg = f"--git-dir={sidekick_git_dir}"

        subprocess.run(["git", git_dir_arg, "add", "."], capture_output=True, timeout=5)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"{message_prefix} - {timestamp}"

        result = subprocess.run(
            ["git", git_dir_arg, "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            return False

        return True
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def perform_undo(session: SessionState) -> Tuple[bool, str]:
    """
    Undo the most recent change by resetting to the previous commit.
    Also adds a system message to the chat history to inform the AI
    that the last changes were undone.

    Args:
        session: The SessionState instance.

    Returns:
        tuple: (bool, str) - Success status and message
    """
    # Get the session directory and git dir
    session_dir = get_session_dir(session)
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
    except subprocess.TimeoutExpired as e:
        error = GitOperationError(
            operation="reset", message="Undo operation timed out", original_error=e
        )
        return False, str(error)
    except Exception as e:
        error = GitOperationError(operation="reset", message=str(e), original_error=e)
        return False, f"Error performing undo: {e}"
