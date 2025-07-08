"""UI module - maintains backward compatibility by re-exporting all functions."""

# Re-export from core
# Re-export from colors
from sidekick.ui.colors import Colors, colors
from sidekick.ui.core import (
    SpinnerStyle,
    banner,
    start_spinner,
    stop_spinner,
)

# Make SYNTAX_THEME available at top level
# Re-export from formatting
from sidekick.ui.formatting import (
    SYNTAX_THEME,
    create_inline_diff,
    create_shell_syntax,
    create_syntax_highlighted,
    create_unified_diff,
    format_server_name,
    get_command_display_name,
    get_file_language,
)

# Re-export from messages
from sidekick.ui.messages import (
    agent,
    bullet,
    dump,
    error,
    help,
    info,
    line,
    muted,
    success,
    update_available,
    usage,
    version,
    warning,
)

# Re-export constants that were in the original ui.py
# Re-export from panels
from sidekick.ui.panels import (
    PANEL_CONTENT_PADDING,
    PANEL_WRAPPER_PADDING,
    PANEL_WRAPPER_PADDING_NO_BOTTOM,
    console,
    create_panel,
    display_agent_panel,
    display_confirmation_panel,
    display_error_panel,
    display_info_panel,
    display_panel,
    display_thinking_panel,
    display_tool_panel,
    reset_output_context,
)

__all__ = [
    # Core
    "THINKING_MESSAGES",
    "SpinnerStyle",
    "banner",
    "get_thinking_message",
    "start_spinner",
    "stop_spinner",
    # Formatting
    "create_inline_diff",
    "create_shell_syntax",
    "create_syntax_highlighted",
    "create_unified_diff",
    "format_server_name",
    "get_command_display_name",
    "get_file_language",
    "SYNTAX_THEME",
    # Messages
    "agent",
    "bullet",
    "dump",
    "error",
    "help",
    "info",
    "line",
    "muted",
    "success",
    "update_available",
    "usage",
    "version",
    "warning",
    # Panels
    "Colors",
    "colors",
    "console",
    "create_panel",
    "display_agent_panel",
    "display_confirmation_panel",
    "display_error_panel",
    "display_info_panel",
    "display_panel",
    "display_tool_panel",
    "display_thinking_panel",
    "reset_output_context",
    # Constants
    "PANEL_CONTENT_PADDING",
    "PANEL_WRAPPER_PADDING",
    "PANEL_WRAPPER_PADDING_NO_BOTTOM",
]
