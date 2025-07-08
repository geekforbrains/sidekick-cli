"""Handle /usage command."""

from rich.text import Text

from sidekick import ui
from sidekick.usage import usage_tracker


async def handle_usage():
    """Handle /usage command - show session usage statistics."""
    content = Text()

    if usage_tracker.total_tokens > 0:
        content.append("Total Statistics\n", style=f"bold {ui.colors.primary}")
        content.append(f"  • Total tokens: {usage_tracker.total_tokens:,}\n", style="white")
        content.append(f"  • Total cost: ${usage_tracker.total_cost:.5f}\n", style="white")
        content.append(f"  • Total requests: {usage_tracker.total_requests:,}\n", style="white")

    if usage_tracker.last_request:
        if usage_tracker.total_tokens > 0:
            content.append("\n")
        content.append("Last Request\n", style=f"bold {ui.colors.primary}")
        content.append(f"  • Model: {usage_tracker.last_request['model']}\n", style="white")
        content.append(
            f"  • Input tokens: {usage_tracker.last_request['input_tokens']:,}\n", style="white"
        )
        content.append(
            f"  • Cached tokens: {usage_tracker.last_request['cached_tokens']:,}\n", style="white"
        )
        content.append(
            f"  • Output tokens: {usage_tracker.last_request['output_tokens']:,}\n", style="white"
        )
        content.append(
            f"  • Request cost: ${usage_tracker.last_request['request_cost']:.5f}\n", style="white"
        )

    if not usage_tracker.total_tokens:
        content.append("No usage data yet in this session", style=ui.colors.muted)

    if content.plain.endswith("\n"):
        content = Text(content.plain.rstrip("\n"))

    panel = ui.create_panel(content, "Session Usage Statistics", ui.colors.muted)
    ui.display_panel(panel)
