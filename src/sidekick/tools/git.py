import subprocess

from pydantic_ai import ModelRetry


async def git_add(files: str) -> str:
    """Stage files for commit using git add.

    Args:
        files: Files to stage (can be paths, patterns, or '.' for all)

    Returns:
        Success message with staged files count
    """
    try:
        # First check git status to show what will be staged
        status_result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )

        if not status_result.stdout.strip():
            return "No changes to stage"

        # Parse files argument - could be '.', specific files, or patterns
        if files.strip() == ".":
            # Stage all changes
            subprocess.run(["git", "add", "."], capture_output=True, text=True, check=True)
        else:
            # Stage specific files/patterns
            file_list = files.split() if " " in files else [files]
            subprocess.run(["git", "add"] + file_list, capture_output=True, text=True, check=True)

        # Get updated status to show what was staged
        new_status = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )

        # Count staged files
        staged_count = sum(
            1 for line in new_status.stdout.splitlines() if line and line[0] in ["A", "M", "D", "R"]
        )

        return f"Successfully staged {staged_count} file(s)"

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise ModelRetry(f"Git add failed: {error_msg}")
    except Exception as e:
        raise ModelRetry(f"Error running git add: {str(e)}")


async def git_commit(message: str) -> str:
    """Create a git commit with the given message.

    Args:
        message: Commit message

    Returns:
        Success message with commit hash
    """
    try:
        # Check if there are staged changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )

        # Check for staged files
        staged_files = [
            line
            for line in status_result.stdout.splitlines()
            if line and line[0] in ["A", "M", "D", "R"]
        ]

        if not staged_files:
            return "No staged changes to commit"

        # Create the commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", message], capture_output=True, text=True, check=True
        )

        # Extract commit hash from output
        output_lines = commit_result.stdout.strip().split("\n")
        commit_info = output_lines[0] if output_lines else "Commit created"

        return f"Successfully created commit: {commit_info}"

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        raise ModelRetry(f"Git commit failed: {error_msg}")
    except Exception as e:
        raise ModelRetry(f"Error running git commit: {str(e)}")
