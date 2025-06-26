"""Debug logging configuration for Sidekick CLI."""

import json
import logging
from datetime import datetime
from typing import Any


def configure_debug_logging() -> str:
    """Configure debug logging when --debug flag is set.

    Returns:
        Path to the log file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"sidekick_{timestamp}.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)-5s - %(name)s - %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8")],
    )

    # Silence noisy modules
    ignored_modules = [
        "httpcore",
        "httpx",
        "urllib3",
        "asyncio",
        "markdown_it",
    ]

    for module in ignored_modules:
        logging.getLogger(module).setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Debug logging initialized to {log_file}")

    return log_file


def log_message_history(messages: list):
    """Write the entire message history to the log file in a readable format."""
    # Get the file handler from the root logger
    handlers = logging.getLogger().handlers
    file_handler = None
    for handler in handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler = handler
            break

    if not file_handler:
        return

    # Write directly to the file
    with open(file_handler.baseFilename, "a", encoding="utf-8") as f:
        f.write("\n\n")
        f.write("=" * 80 + "\n")
        f.write("MESSAGE HISTORY DUMP\n")
        f.write("=" * 80 + "\n\n")

        for i, message in enumerate(messages):
            f.write(f"Message {i + 1}:\n")
            f.write("-" * 40 + "\n")

            try:
                if hasattr(message, "__dict__"):
                    f.write(json.dumps(message.__dict__, indent=2, default=str))
                else:
                    f.write(str(message))
            except Exception as e:
                f.write(f"Error formatting message: {e}\n")
                f.write(repr(message))

            f.write("\n\n")

        f.write("=" * 80 + "\n")
        f.write("END OF MESSAGE HISTORY\n")
        f.write("=" * 80 + "\n")


def format_for_logging(data: Any) -> str:
    """Format data for logging."""
    try:
        if hasattr(data, "__dict__"):
            return json.dumps(data.__dict__, indent=2, default=str)
        elif isinstance(data, (dict, list)):
            return json.dumps(data, indent=2, default=str)
        else:
            return str(data)
    except Exception:
        return repr(data)
