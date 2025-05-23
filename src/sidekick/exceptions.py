"""
Sidekick CLI exception hierarchy.

This module defines all custom exceptions used throughout the Sidekick CLI.
All exceptions inherit from SidekickError for easy catching of any Sidekick-specific error.
"""


class SidekickError(Exception):
    """Base exception for all Sidekick errors."""

    pass


# Configuration and Setup Exceptions
class ConfigurationError(SidekickError):
    """Raised when there's a configuration issue."""

    pass


class SidekickConfigError(ConfigurationError):
    """Legacy alias for ConfigurationError. Kept for backward compatibility."""

    pass


# User Interaction Exceptions
class UserAbortError(SidekickError):
    """Raised when user aborts an operation."""

    pass


class SidekickAbort(UserAbortError):
    """Legacy alias for UserAbortError. Kept for backward compatibility."""

    pass


class ValidationError(SidekickError):
    """Raised when input validation fails."""

    pass


# Tool and Agent Exceptions
class ToolExecutionError(SidekickError):
    """Raised when a tool fails to execute."""

    def __init__(self, tool_name: str, message: str, original_error: Exception = None):
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class AgentError(SidekickError):
    """Raised when agent operations fail."""

    pass


# State Management Exceptions
class StateError(SidekickError):
    """Raised when there's an issue with application state."""

    pass


# External Service Exceptions
class ServiceError(SidekickError):
    """Base exception for external service failures."""

    pass


class MCPError(ServiceError):
    """Raised when MCP server operations fail."""

    def __init__(self, server_name: str, message: str, original_error: Exception = None):
        self.server_name = server_name
        self.original_error = original_error
        super().__init__(f"MCP server '{server_name}' error: {message}")


class TelemetryError(ServiceError):
    """Raised when telemetry operations fail."""

    pass


class GitOperationError(ServiceError):
    """Raised when Git operations fail."""

    def __init__(self, operation: str, message: str, original_error: Exception = None):
        self.operation = operation
        self.original_error = original_error
        super().__init__(f"Git {operation} failed: {message}")


# File System Exceptions
class FileOperationError(SidekickError):
    """Raised when file system operations fail."""

    def __init__(self, operation: str, path: str, message: str, original_error: Exception = None):
        self.operation = operation
        self.path = path
        self.original_error = original_error
        super().__init__(f"File {operation} failed for '{path}': {message}")
