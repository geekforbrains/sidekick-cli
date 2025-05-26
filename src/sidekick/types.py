"""
Centralized type definitions for Sidekick CLI.

This module contains all type aliases, protocols, and type definitions
used throughout the Sidekick codebase.
"""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, Protocol, Tuple, Union

# Try to import pydantic-ai types if available
try:
    from pydantic_ai import Agent
    from pydantic_ai.messages import ModelRequest, ModelResponse, ToolReturnPart

    PydanticAgent = Agent
    MessagePart = Union[ToolReturnPart, Any]
except ImportError:
    # Fallback if pydantic-ai is not available
    PydanticAgent = Any
    MessagePart = Any
    ModelRequest = Any
    ModelResponse = Any

# =============================================================================
# Core Types
# =============================================================================

# Basic type aliases
UserConfig = dict[str, Any]
EnvConfig = dict[str, str]
ModelName = str
ToolName = str
SessionId = str
DeviceId = str
InputSessions = dict[str, Any]

# =============================================================================
# Configuration Types
# =============================================================================


@dataclass
class ModelPricing:
    """Pricing information for a model."""

    input: float
    cached_input: float
    output: float


@dataclass
class ModelConfig:
    """Configuration for a model including pricing."""

    pricing: ModelPricing


ModelRegistry = dict[str, ModelConfig]

# Path configuration
ConfigPath = Path
ConfigFile = Path

# =============================================================================
# Tool Types
# =============================================================================

# Tool execution types
ToolArgs = dict[str, Any]
ToolResult = str
ToolCallback = Callable[[Any, Any], Awaitable[None]]
ToolCallId = str


class ToolFunction(Protocol):
    """Protocol for tool functions."""

    async def __call__(self, *args, **kwargs) -> str: ...


@dataclass
class ToolConfirmationRequest:
    """Request for tool execution confirmation."""

    tool_name: str
    args: dict[str, Any]
    filepath: Optional[str] = None


@dataclass
class ToolConfirmationResponse:
    """Response from tool confirmation dialog."""

    approved: bool
    skip_future: bool = False
    abort: bool = False


# =============================================================================
# UI Types
# =============================================================================


class UILogger(Protocol):
    """Protocol for UI logging operations."""

    async def info(self, message: str) -> None: ...
    async def error(self, message: str) -> None: ...
    async def warning(self, message: str) -> None: ...
    async def debug(self, message: str) -> None: ...
    async def success(self, message: str) -> None: ...


# UI callback types
UICallback = Callable[[str], Awaitable[None]]
UIInputCallback = Callable[[str, str], Awaitable[str]]

# =============================================================================
# Agent Types
# =============================================================================

# Agent response types
AgentResponse = Any  # Replace with proper pydantic-ai types when available
MessageHistory = list[Any]
AgentRun = Any  # pydantic_ai.RunContext or similar

# Agent configuration
AgentConfig = dict[str, Any]
AgentName = str

# =============================================================================
# Session and State Types
# =============================================================================


@dataclass
class SessionState:
    """Complete session state for the application."""

    user_config: dict[str, Any] = field(default_factory=dict)
    agents: dict[str, Any] = field(default_factory=dict)
    messages: list[Any] = field(default_factory=list)
    total_cost: float = 0.0
    current_model: str = "openai:gpt-4o"
    spinner: Optional[Any] = None
    tool_ignore: list[str] = field(default_factory=list)
    yolo: bool = False
    undo_initialized: bool = False
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    device_id: Optional[str] = None
    telemetry_enabled: bool = True
    input_sessions: dict[str, Any] = field(default_factory=dict)
    current_task: Optional[Any] = None

    def reset(self):
        """Reset the session state to initial values."""
        self.__init__()


# =============================================================================
# Command Types
# =============================================================================

# Command execution types
CommandArgs = list[str]
CommandResult = Optional[Any]
ProcessRequestCallback = Callable[[str, "SessionState", bool], Awaitable[Any]]


@dataclass
class CommandContext:
    """Context passed to command handlers."""

    session: SessionState
    process_request: Optional[ProcessRequestCallback] = None


# =============================================================================
# Service Types
# =============================================================================

# MCP (Model Context Protocol) types
MCPServerConfig = dict[str, Any]
MCPServers = dict[str, MCPServerConfig]

# Telemetry types
TelemetryEvent = dict[str, Any]
TelemetryData = dict[str, Any]

# =============================================================================
# File Operation Types
# =============================================================================

# File-related types
FilePath = Union[str, Path]
FileContent = str
FileEncoding = str
FileDiff = Tuple[str, str]  # (original, modified)
FileSize = int
LineNumber = int

# =============================================================================
# Error Handling Types
# =============================================================================

# Error context types
ErrorContext = dict[str, Any]
OriginalError = Optional[Exception]
ErrorMessage = str

# =============================================================================
# Async Types
# =============================================================================

# Async function types
AsyncFunc = Callable[..., Awaitable[Any]]
AsyncToolFunc = Callable[..., Awaitable[str]]
AsyncVoidFunc = Callable[..., Awaitable[None]]

# =============================================================================
# Diff and Update Types
# =============================================================================

# Types for file updates and diffs
UpdateOperation = dict[str, Any]
DiffLine = str
DiffHunk = list[DiffLine]

# =============================================================================
# Validation Types
# =============================================================================

# Input validation types
ValidationResult = Union[bool, str]  # True for valid, error message for invalid
Validator = Callable[[Any], ValidationResult]

# =============================================================================
# Cost Tracking Types
# =============================================================================

# Cost calculation types
TokenCount = int
CostAmount = float


@dataclass
class TokenUsage:
    """Token usage for a request."""

    input_tokens: int
    cached_tokens: int
    output_tokens: int


@dataclass
class CostBreakdown:
    """Breakdown of costs for a request."""

    input_cost: float
    cached_cost: float
    output_cost: float
    total_cost: float
