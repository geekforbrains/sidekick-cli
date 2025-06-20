import functools
import subprocess
from typing import Any, Callable, TypeVar

from sidekick import ui

T = TypeVar("T")


def handle_tool_errors(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to handle common tool errors consistently."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except FileNotFoundError:
            # Extract filepath from args if available
            filepath = args[0] if args else "unknown"
            err_msg = f"File not found: {filepath}"
            ui.error(err_msg)
            return err_msg
        except subprocess.TimeoutExpired:
            err_msg = "Command timed out after 30 seconds"
            ui.error(err_msg)
            return err_msg
        except Exception as e:
            # Determine error prefix based on function name
            operation = func.__name__.replace("_", " ")
            err_msg = f"Error {operation}: {str(e)}"
            ui.error(err_msg)
            return err_msg

    return wrapper
