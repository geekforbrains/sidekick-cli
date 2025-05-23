"""
Module: sidekick.ui.decorators

Provides decorators for UI functions including sync/async wrapper patterns.
"""

import asyncio
from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def create_sync_wrapper(async_func: F) -> F:
    """Create a synchronous wrapper for an async function.

    This decorator does NOT modify the original async function.
    Instead, it attaches a sync version as a 'sync' attribute.

    Args:
        async_func: The async function to wrap

    Returns:
        The original async function with sync version attached
    """

    @wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use run_until_complete
                # This might happen when called from within an async function
                raise RuntimeError(
                    f"Cannot call sync_{async_func.__name__} from within an async context. "
                    f"Use await {async_func.__name__}() instead."
                )
        except RuntimeError:
            # No event loop exists, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(async_func(*args, **kwargs))

    # Set a naming convention
    sync_wrapper.__name__ = f"sync_{async_func.__name__}"
    sync_wrapper.__qualname__ = f"sync_{async_func.__qualname__}"

    # Update docstring to indicate this is a sync version
    if async_func.__doc__:
        sync_wrapper.__doc__ = (
            f"Synchronous version of {async_func.__name__}.\n\n{async_func.__doc__}"
        )

    # Attach the sync version as an attribute
    async_func.sync = sync_wrapper

    # Return the original async function
    return async_func
