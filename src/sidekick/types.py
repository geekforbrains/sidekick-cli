"""
Centralized type definitions for Sidekick CLI.

This module contains all type aliases, protocols, and type definitions
used throughout the Sidekick codebase.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol, Tuple, Union

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
UserConfig = Dict[str, Any]
EnvConfig = Dict[str, str]
ModelName = str
ToolName = str
SessionId = str
DeviceId = str
InputSessions = Dict[str, Any]

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


ModelRegistry = Dict[str, ModelConfig]

# Path configuration
ConfigPath = Path
ConfigFile = Path

# =============================================================================
# Tool Types
# =============================================================================

# Tool execution types
ToolArgs = Dict[str, Any]
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
    args: Dict[str, Any]
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
MessageHistory = List[Any]
AgentRun = Any  # pydantic_ai.RunContext or similar

# Agent configuration
AgentConfig = Dict[str, Any]
AgentName = str

# =============================================================================
# Session and State Types
# =============================================================================


@dataclass
class SessionState:
    """Complete session state for the application."""

    user_config: Dict[str, Any]
    agents: Dict[str, Any]
    messages: List[Any]
    total_cost: float
    current_model: str
    spinner: Optional[Any]
    tool_ignore: List[str]
    yolo: bool
    undo_initialized: bool
    session_id: str
    device_id: Optional[str]
    telemetry_enabled: bool
    input_sessions: Dict[str, Any]
    current_task: Optional[Any]


# Forward reference for StateManager to avoid circular imports
StateManager = Any  # Will be replaced with actual StateManager type

# =============================================================================
# Command Types
# =============================================================================

# Command execution types
CommandArgs = List[str]
CommandResult = Optional[Any]
ProcessRequestCallback = Callable[[str, StateManager, bool], Awaitable[Any]]


@dataclass
class CommandContext:
    """Context passed to command handlers."""

    state_manager: StateManager
    process_request: Optional[ProcessRequestCallback] = None


# =============================================================================
# Service Types
# =============================================================================

# MCP (Model Context Protocol) types
MCPServerConfig = Dict[str, Any]
MCPServers = Dict[str, MCPServerConfig]

# Telemetry types
TelemetryEvent = Dict[str, Any]
TelemetryData = Dict[str, Any]

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
ErrorContext = Dict[str, Any]
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
UpdateOperation = Dict[str, Any]
DiffLine = str
DiffHunk = List[DiffLine]

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
