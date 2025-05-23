"""User input handling functions for Sidekick UI."""

from typing import Optional

from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.validation import Validator

from sidekick.constants import UI_PROMPT_PREFIX
from sidekick.core.state import StateManager

from .keybindings import create_key_bindings
from .prompt_manager import PromptConfig, PromptManager


def formatted_text(text: str) -> HTML:
    """Create formatted HTML text."""
    return HTML(text)


async def input(
    session_key: str,
    pretext: str = UI_PROMPT_PREFIX,
    is_password: bool = False,
    validator: Optional[Validator] = None,
    multiline: bool = False,
    key_bindings: Optional[KeyBindings] = None,
    placeholder: Optional[HTML] = None,
    timeoutlen: float = 0.05,
    state_manager: Optional[StateManager] = None,
) -> str:
    """
    Prompt for user input using simplified prompt management.

    Args:
        session_key: The session key for the prompt
        pretext: The text to display before the input prompt
        is_password: Whether to mask the input
        validator: Optional input validator
        multiline: Whether to allow multiline input
        key_bindings: Optional custom key bindings
        placeholder: Optional placeholder text
        timeoutlen: Timeout length for input
        state_manager: The state manager for session storage

    Returns:
        User input string
    """
    # Create prompt configuration
    config = PromptConfig(
        multiline=multiline,
        is_password=is_password,
        validator=validator,
        key_bindings=key_bindings,
        placeholder=placeholder,
        timeoutlen=timeoutlen,
    )

    # Create prompt manager
    manager = PromptManager(state_manager)

    # Get user input
    return await manager.get_input(session_key, pretext, config)


async def multiline_input() -> str:
    """Get multiline input from the user."""
    kb = create_key_bindings()
    placeholder = formatted_text(
        (
            "<darkgrey>"
            "<bold>Enter</bold> to submit, "
            "<bold>Esc + Enter</bold> for new line, "
            "<bold>/help</bold> for commands"
            "</darkgrey>"
        )
    )
    return await input("multiline", key_bindings=kb, multiline=True, placeholder=placeholder)
