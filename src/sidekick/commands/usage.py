"""Handle /usage command."""

from rich.text import Text

from sidekick import ui
from sidekick.session import session


async def handle_usage():
    """Handle /usage command - show session usage statistics."""
    content = Text()

    if session.total_tokens > 0:
        content.append("Total Statistics\n", style=f"bold {ui.colors.primary}")
        content.append(f"  • Total tokens: {session.total_tokens:,}\n", style="white")
        content.append(f"  • Total cost: ${session.total_cost:.5f}\n", style="white")

    if session.last_usage:
        if session.total_tokens > 0:
            content.append("\n")
        content.append("Last Request\n", style=f"bold {ui.colors.primary}")
        content.append(f"  • Input tokens: {session.last_usage['input_tokens']:,}\n", style="white")
        content.append(
            f"  • Cached tokens: {session.last_usage['cached_tokens']:,}\n", style="white"
        )
        content.append(
            f"  • Output tokens: {session.last_usage['output_tokens']:,}\n", style="white"
        )
        content.append(
            f"  • Request cost: ${session.last_usage['request_cost']:.5f}\n", style="white"
        )

    if not session.total_tokens:
        content.append("No usage data yet in this session", style=ui.colors.muted)

    if content.plain.endswith("\n"):
        content = Text(content.plain.rstrip("\n"))

    panel = ui.create_panel(content, "Session Usage Statistics", ui.colors.muted)
    ui.display_panel(panel)
