"""Special UI functions that need external dependencies."""

from rich.padding import Padding
from rich.text import Text

from sidekick.constants import APP_NAME, APP_VERSION, MODELS
from sidekick.session import session
from sidekick.ui.colors import colors
from sidekick.usage import usage_tracker


def version(ui_manager):
    """Display version information."""
    ui_manager.console.print(f"{APP_NAME} v{APP_VERSION}", style=colors.muted)


def update_available(ui_manager, latest_version: str):
    """Display update available message."""
    ui_manager.muted(f"Update available: {APP_VERSION} → {latest_version}")


def usage(ui_manager, usage_data: dict):
    """Display usage statistics."""
    content = Text()
    content.append("Input: ", style=colors.muted)
    content.append(f"{usage_data['input_tokens']:,} tokens")
    if usage_data["cached_tokens"] > 0:
        content.append(f" ({usage_data['cached_tokens']:,} cached)", style=colors.muted)

    content.append(" | ", style=colors.muted)
    content.append("Output: ", style=colors.muted)
    content.append(f"{usage_data['output_tokens']:,} tokens")

    content.append(" | ", style=colors.muted)
    content.append("Cost: ", style=colors.muted)
    content.append(f"${usage_data['request_cost']:.5f}")

    if session.current_model and usage_tracker.total_tokens:
        model_info = MODELS.get(session.current_model)
        if model_info and "context_window" in model_info:
            token_limit = model_info["context_window"]
            if token_limit > 0:
                remaining_percentage = (
                    (token_limit - usage_tracker.total_tokens) / token_limit
                ) * 100
                # Ensure percentage doesn't go below 0
                remaining_percentage = max(0, remaining_percentage)
                content.append(" | ", style=colors.muted)
                content.append(f"{remaining_percentage:.0f}% ")
                content.append("Context remaining", style=colors.muted)

    ui_manager.console.print(Padding(content, (0, 0, 0, 2)))
