"""User input handling functions for Sidekick UI."""

from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.validation import Validator

from sidekick.constants import UI_PROMPT_PREFIX
from sidekick.core.state import StateManager
from sidekick.exceptions import UserAbortError

from .keybindings import create_key_bindings


def formatted_text(text: str):
    """Create formatted HTML text."""
    return HTML(text)


async def input(
    session_key: str,
    pretext: str = UI_PROMPT_PREFIX,
    is_password: bool = False,
    validator: Validator = None,
    multiline=False,
    key_bindings=None,
    placeholder=None,
    timeoutlen=0.05,
    state_manager: StateManager = None,
):
    """
    Prompt for user input. Creates session for given key if it doesn't already exist.

    Args:
        session_key (str): The session key for the prompt.
        pretext (str): The text to display before the input prompt.
        is_password (bool): Whether to mask the input.
        state_manager (StateManager): The state manager for session storage.

    """
    if state_manager:
        if session_key not in state_manager.session.input_sessions:
            state_manager.session.input_sessions[session_key] = PromptSession(
                key_bindings=key_bindings,
                placeholder=placeholder,
            )
        prompt_session = state_manager.session.input_sessions[session_key]
    else:
        # Create a temporary session if no state manager
        prompt_session = PromptSession(
            key_bindings=key_bindings,
            placeholder=placeholder,
        )

    try:
        # # Ensure prompt is displayed correctly even after async output
        # await run_in_terminal(lambda: prompt_session.app.invalidate())
        resp = await prompt_session.prompt_async(
            pretext,
            is_password=is_password,
            validator=validator,
            multiline=multiline,
        )
        if isinstance(resp, str):
            resp = resp.strip()
        return resp
    except KeyboardInterrupt:
        raise UserAbortError
    except EOFError:
        raise UserAbortError


async def multiline_input():
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
