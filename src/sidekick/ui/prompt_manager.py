"""Prompt configuration and management for Sidekick UI."""

from dataclasses import dataclass
from typing import Optional

from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.validation import Validator

from sidekick.exceptions import UserAbortError
from sidekick.types import SessionState


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

    def __init__(self, session: Optional[SessionState] = None):
        """Initialize the prompt manager.

        Args:
            session: Optional session state for session persistence
        """
        self.session = session
        self._temp_sessions = {}  # For when no session state is available

    def get_session(self, session_key: str, config: PromptConfig) -> PromptSession:
        """Get or create a prompt session.

        Args:
            session_key: Unique key for the session
            config: Configuration for the session

        Returns:
            PromptSession instance
        """
        if self.session:
            # Use session state's session storage
            if session_key not in self.session.input_sessions:
                self.session.input_sessions[session_key] = PromptSession(
                    key_bindings=config.key_bindings,
                    placeholder=config.placeholder,
                )
            return self.session.input_sessions[session_key]
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
            response = await session.prompt_async(
                prompt,
                is_password=config.is_password,
                validator=config.validator,
                multiline=config.multiline,
            )

            if isinstance(response, str):
                response = response.strip()

            return response

        except (KeyboardInterrupt, EOFError):
            raise UserAbortError
