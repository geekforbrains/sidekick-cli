"""Prompt configuration and management for Sidekick UI."""

from dataclasses import dataclass
from typing import Optional

from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.validation import Validator

from sidekick.core.state import StateManager
from sidekick.exceptions import UserAbortError


@dataclass
class PromptConfig:
    """Configuration for prompt sessions."""

    multiline: bool = False
    is_password: bool = False
    validator: Optional[Validator] = None
    key_bindings: Optional[KeyBindings] = None
    placeholder: Optional[FormattedText] = None
    timeoutlen: float = 0.05


class PromptManager:
    """Manages prompt sessions and their lifecycle."""

    def __init__(self, state_manager: Optional[StateManager] = None):
        """Initialize the prompt manager.

        Args:
            state_manager: Optional state manager for session persistence
        """
        self.state_manager = state_manager
        self._temp_sessions = {}  # For when no state manager is available

    def get_session(self, session_key: str, config: PromptConfig) -> PromptSession:
        """Get or create a prompt session.

        Args:
            session_key: Unique key for the session
            config: Configuration for the session

        Returns:
            PromptSession instance
        """
        if self.state_manager:
            # Use state manager's session storage
            if session_key not in self.state_manager.session.input_sessions:
                self.state_manager.session.input_sessions[session_key] = PromptSession(
                    key_bindings=config.key_bindings,
                    placeholder=config.placeholder,
                )
            return self.state_manager.session.input_sessions[session_key]
        else:
            # Use temporary storage
            if session_key not in self._temp_sessions:
                self._temp_sessions[session_key] = PromptSession(
                    key_bindings=config.key_bindings,
                    placeholder=config.placeholder,
                )
            return self._temp_sessions[session_key]

    async def get_input(self, session_key: str, prompt: str, config: PromptConfig) -> str:
        """Get user input using the specified configuration.

        Args:
            session_key: Unique key for the session
            prompt: The prompt text to display
            config: Configuration for the input

        Returns:
            User input string

        Raises:
            UserAbortError: If user cancels input
        """
        session = self.get_session(session_key, config)

        try:
            # Get user input
            response = await session.prompt_async(
                prompt,
                is_password=config.is_password,
                validator=config.validator,
                multiline=config.multiline,
            )

            # Clean up response
            if isinstance(response, str):
                response = response.strip()

            return response

        except (KeyboardInterrupt, EOFError):
            raise UserAbortError
