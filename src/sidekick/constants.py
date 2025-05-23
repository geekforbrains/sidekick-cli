# Application info
APP_NAME = "Sidekick"
APP_VERSION = "0.4.1"

# File patterns
GUIDE_FILE_PATTERN = "{name}.md"
GUIDE_FILE_NAME = "SIDEKICK.md"
ENV_FILE = ".env"
CONFIG_FILE_NAME = "sidekick.json"

# Default limits
MAX_FILE_SIZE = 100 * 1024  # 100KB
MAX_COMMAND_OUTPUT = 5000  # 5000 chars

# Command output processing
COMMAND_OUTPUT_THRESHOLD = 3500  # Length threshold for truncation
COMMAND_OUTPUT_START_INDEX = 2500  # Where to start showing content
COMMAND_OUTPUT_END_SIZE = 1000  # How much to show from the end

# Tool names
TOOL_READ_FILE = "read_file"
TOOL_WRITE_FILE = "write_file"
TOOL_UPDATE_FILE = "update_file"
TOOL_RUN_COMMAND = "run_command"

# Commands
CMD_HELP = "/help"
CMD_CLEAR = "/clear"
CMD_DUMP = "/dump"
CMD_YOLO = "/yolo"
CMD_UNDO = "/undo"
CMD_COMPACT = "/compact"
CMD_MODEL = "/model"
CMD_EXIT = "exit"
CMD_QUIT = "quit"

# Command descriptions
DESC_HELP = "Show this help message"
DESC_CLEAR = "Clear the conversation history"
DESC_DUMP = "Show the current conversation history"
DESC_YOLO = "Toggle confirmation prompts on/off"
DESC_UNDO = "Undo the last file change"
DESC_COMPACT = "Summarize the conversation context"
DESC_MODEL = "List available models"
DESC_MODEL_SWITCH = "Switch to a specific model"
DESC_MODEL_DEFAULT = "Set a model as the default"
DESC_EXIT = "Exit the application"

# Command Configuration
COMMAND_PREFIX = "/"
COMMAND_CATEGORIES = {
    "state": ["yolo", "undo"],
    "debug": ["dump", "compact"],
    "ui": ["clear", "help"],
    "config": ["model"],
}

# System paths
SIDEKICK_HOME_DIR = ".sidekick"
SESSIONS_SUBDIR = "sessions"
DEVICE_ID_FILE = "device_id"

# UI colors
UI_COLORS = {
    "primary": "medium_purple1",
    "secondary": "medium_purple3",
    "success": "green",
    "warning": "orange1",
    "error": "red",
    "muted": "grey62",
}

# UI text and formatting
UI_PROMPT_PREFIX = "λ "
UI_THINKING_MESSAGE = "[bold green]Thinking..."
UI_DARKGREY_OPEN = "<darkgrey>"
UI_DARKGREY_CLOSE = "</darkgrey>"
UI_BOLD_OPEN = "<bold>"
UI_BOLD_CLOSE = "</bold>"
UI_KEY_ENTER = "Enter"
UI_KEY_ESC_ENTER = "Esc + Enter"

# Panel titles
PANEL_ERROR = "Error"
PANEL_MESSAGE_HISTORY = "Message History"
PANEL_MODELS = "Models"
PANEL_AVAILABLE_COMMANDS = "Available Commands"

# Error messages
ERROR_PROVIDER_EMPTY = "Provider number cannot be empty"
ERROR_INVALID_PROVIDER = "Invalid provider number"
ERROR_FILE_NOT_FOUND = "Error: File not found at '{filepath}'."
ERROR_FILE_TOO_LARGE = "Error: File '{filepath}' is too large (> 100KB)."
ERROR_FILE_DECODE = "Error reading file '{filepath}': Could not decode using UTF-8."
ERROR_FILE_DECODE_DETAILS = "It might be a binary file or use a different encoding. {error}"
ERROR_COMMAND_NOT_FOUND = "Error: Command not found or failed to execute:"
ERROR_COMMAND_EXECUTION = (
    "Error: Command not found or failed to execute: {command}. Details: {error}"
)
ERROR_UNDO_INIT = "Error initializing undo system: {e}"

# Command output messages
CMD_OUTPUT_NO_OUTPUT = "No output."
CMD_OUTPUT_NO_ERRORS = "No errors."
CMD_OUTPUT_FORMAT = "STDOUT:\n{output}\n\nSTDERR:\n{error}"
CMD_OUTPUT_TRUNCATED = "\n...\n[truncated]\n...\n"

# Undo system messages
UNDO_DISABLED_HOME = "Undo system disabled, running from home directory"
UNDO_DISABLED_NO_GIT = "Undo system disabled, not in a git project"
UNDO_INITIAL_COMMIT = "Initial commit for sidekick undo history"
UNDO_GIT_TIMEOUT = "Git initialization timed out"

# Log/status messages
MSG_UPDATE_AVAILABLE = "Update available: v{latest_version}"
MSG_UPDATE_INSTRUCTION = "Exit, and run: [bold]pip install --upgrade sidekick-cli"
MSG_VERSION_DISPLAY = "Sidekick CLI {version}"
MSG_FILE_SIZE_LIMIT = " Please specify a smaller file or use other tools to process it."
