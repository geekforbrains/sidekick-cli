import os
import subprocess
import time
from pathlib import Path

from .. import session


def get_sidekick_home():
    """
    Get the path to the Sidekick home directory (~/.sidekick).
    Creates it if it doesn't exist.
    
    Returns:
        Path: The path to the Sidekick home directory.
    """
    home = Path.home() / ".sidekick"
    home.mkdir(exist_ok=True)
    return home


def get_session_dir():
    """
    Get the path to the current session directory.
    
    Returns:
        Path: The path to the current session directory.
    """
    # Generate a new session ID if we don't have one
    if session.session_id is None:
        import uuid
        session.session_id = str(uuid.uuid4())
    
    session_dir = get_sidekick_home() / "sessions" / session.session_id
    session_dir.mkdir(exist_ok=True, parents=True)
    return session_dir


def init_undo_system():
    """
    Initialize the undo system by creating a Git repository
    in the ~/.sidekick/sessions/<session-id> directory.
    
    Returns:
        bool: True if the undo system was initialized, False otherwise.
    """
    # Get the session directory path
    session_dir = get_session_dir()
    sidekick_git_dir = session_dir / ".git"
    
    # Check if already initialized
    if sidekick_git_dir.exists():
        return True
    
    # Initialize Git repository
    try:
        subprocess.run(
            ["git", "init", str(session_dir)],
            capture_output=True,
            check=True
        )
        
        # Make an initial commit
        git_dir_arg = f"--git-dir={sidekick_git_dir}"
        
        # Add all files
        subprocess.run(
            ["git", git_dir_arg, "add", "."],
            capture_output=True,
            check=True
        )
        
        # Create initial commit
        subprocess.run(
            ["git", git_dir_arg, "commit", "-m", "Initial commit for sidekick undo history"],
            capture_output=True,
            check=True
        )
        
        return True
    except Exception as e:
        print(f"Error initializing undo system: {e}")
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
        subprocess.run(
            ["git", git_dir_arg, "add", "."],
            capture_output=True
        )
        
        # Create commit with timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"{message_prefix} - {timestamp}"
        
        result = subprocess.run(
            ["git", git_dir_arg, "commit", "-m", commit_message],
            capture_output=True,
            text=True
        )
        
        # Handle case where there are no changes to commit
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            return False
            
        return True
    except Exception as e:
        print(f"Error creating undo commit: {e}")
        return False


def perform_undo():
    """
    Undo the most recent change by resetting to the previous commit.
    
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
            check=True
        )
        
        commits = result.stdout.strip().split("\n")
        if len(commits) < 2:
            return False, "Nothing to undo"
        
        # Perform reset to previous commit
        subprocess.run(
            ["git", git_dir_arg, "reset", "--hard", "HEAD~1"],
            capture_output=True,
            check=True
        )
        
        return True, "Successfully undid last change"
    except Exception as e:
        return False, f"Error performing undo: {e}"