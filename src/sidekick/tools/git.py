import asyncio
import subprocess

from pydantic_ai import ModelRetry, RunContext

from sidekick.deps import ToolDeps


async def git_add(ctx: RunContext[ToolDeps], files: str) -> str:
    """Stage files for commit using git add.

    Args:
        files: Files to stage (can be paths, patterns, or '.' for all)

    Returns:
        Success message with staged files count
    """
    # Ignore for now, we already show panel
    #
    # if ctx.deps and ctx.deps.display_tool_status:
    #     await ctx.deps.display_tool_status("Git Add", f"{len(files)} files")

    try:
        # First check git status to show what will be staged
        status_result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )

        if not status_result.stdout.strip():
            return "No changes to stage"

        if ctx.deps and ctx.deps.confirm_action:
            files_to_stage = []
            for line in status_result.stdout.splitlines():
                if line.strip():
                    status = line[:2]
                    filename = line[3:]
                    if files.strip() == "." or any(
                        f in filename for f in (files.split() if " " in files else [files])
                    ):
                        files_to_stage.append(f"{status} {filename}")

            if files_to_stage:
                preview = "\n".join(files_to_stage[:20])
                if len(files_to_stage) > 20:
                    preview += f"\n... and {len(files_to_stage) - 20} more files"

                if not await ctx.deps.confirm_action("Git Add", preview):
                    raise asyncio.CancelledError("Tool execution cancelled by user")

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


async def git_commit(ctx: RunContext[ToolDeps], message: str) -> str:
    """Create a git commit with the given message.

    Args:
        message: Commit message

    Returns:
        Success message with commit hash
    """
    # Ignore for now, we already show panel
    #
    # if ctx.deps and ctx.deps.display_tool_status:
    #     short_message = message[:25].replace("\n", " ")
    #     await ctx.deps.display_tool_status("Git Commit", short_message)

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

        if ctx.deps and ctx.deps.confirm_action:
            preview = f"Message: {message}\n\nStaged changes:\n\n"
            preview += "\n".join(staged_files[:20])
            if len(staged_files) > 20:
                preview += f"\n... and {len(staged_files) - 20} more files"

            if not await ctx.deps.confirm_action("Git Commit", preview):
                raise asyncio.CancelledError("Tool execution cancelled by user")

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
