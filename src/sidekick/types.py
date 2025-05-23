from typing import Any, Dict, List, Protocol

# Configuration types
UserConfig = Dict[str, Any]
EnvConfig = Dict[str, str]
ModelName = str
ToolName = str


# Tool types
class ToolFunction(Protocol):
    async def __call__(self, *args, **kwargs) -> str: ...


# UI types
class UILogger(Protocol):
    async def info(self, message: str) -> None: ...
    async def error(self, message: str) -> None: ...
    async def warning(self, message: str) -> None: ...


# Agent types
AgentResponse = Any  # Replace with proper pydantic-ai types
MessageHistory = List[Any]
