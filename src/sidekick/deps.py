from dataclasses import dataclass
from typing import Awaitable, Callable, Optional


@dataclass
class ToolDeps:
    """Dependencies passed to tools via RunContext."""

    confirm_action: Optional[Callable[[str, str, Optional[str]], Awaitable[bool]]] = None
