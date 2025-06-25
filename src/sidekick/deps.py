from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional


@dataclass
class ToolDeps:
    """Dependencies passed to tools via RunContext."""

    confirm_action: Optional[Callable[[str, str, Optional[str]], Awaitable[bool]]] = None
    display_tool_status: Optional[Callable[[str, Any], Awaitable[None]]] = None
