"""Input utilities for the Sidekick CLI."""

from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML, to_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

# Note: We don't import colors from ui module because prompt_toolkit
# uses a different color system than Rich

PROMPT_SYMBOL = "> "
PROMPT_CONTINUATION_INDENT = "  "  # Same width as prompt symbol
PLACEHOLDER_TEXT = "Esc+Enter to submit, /help for commands"
PLACEHOLDER_STYLE = "italic fg:#666666"


def create_multiline_keybindings() -> KeyBindings:
    """Create key bindings for multiline input.

    Returns:
        KeyBindings configured for ESC+Enter to submit.
    """
    bindings = KeyBindings()

    @bindings.add("escape", "enter")
    def _handle_multiline_submit(event):
        """Accept the buffer on ESC+Enter."""
        event.current_buffer.validate_and_handle()

    return bindings


def create_prompt_style() -> Style:
    """Create consistent style for prompts.

    Returns:
        Style dictionary for prompt_toolkit.
    """
    return Style.from_dict(
        {
            "placeholder": PLACEHOLDER_STYLE,
        }
    )


def prompt_continuation(width: int, line_number: int, is_soft_wrap: bool) -> str:
    """Provide continuation prompt for multiline input.

    Args:
        width: Terminal width (unused)
        line_number: Current line number (unused)
        is_soft_wrap: Whether this is a soft wrap (unused)

    Returns:
        Continuation prompt string.
    """
    return PROMPT_CONTINUATION_INDENT


def create_multiline_prompt_session() -> PromptSession:
    """Create a configured prompt session for multiline input.

    Returns:
        PromptSession configured for multiline input with ESC+Enter submission.
    """
    placeholder_tokens = [("class:placeholder", PLACEHOLDER_TEXT)]
    placeholder_ft = to_formatted_text(placeholder_tokens)

    prompt_html = HTML(f"<ansicyan>{PROMPT_SYMBOL}</ansicyan>")

    return PromptSession(
        message=prompt_html,
        style=create_prompt_style(),
        placeholder=placeholder_ft,
        key_bindings=create_multiline_keybindings(),
        multiline=True,
        prompt_continuation=prompt_continuation,
    )


async def get_multiline_input(session: Optional[PromptSession] = None) -> str:
    """Get multiline input from the user.

    Args:
        session: Optional existing PromptSession. If not provided, a new one is created.

    Returns:
        The user's input, stripped of leading/trailing whitespace.

    Raises:
        EOFError: When Ctrl+D is pressed
        KeyboardInterrupt: When Ctrl+C is pressed
    """
    if session is None:
        session = create_multiline_prompt_session()

    return (await session.prompt_async()).strip()
