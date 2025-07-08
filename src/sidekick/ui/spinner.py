"""Spinner management for the UI module."""

import asyncio
import random
from typing import Optional

from rich.console import Console


class SpinnerManager:
    """Manages spinner state and rotation task."""

    _THINKING_MESSAGES = [
        "Cracking knuckles...",
        "Polishing grappling hook...",
        "Consulting the manual...",
        "Adjusting utility belt...",
        "Calibrating gadgets...",
        "Dusting off cape...",
        "Sharpening batarangs...",
        "Pressing buttons...",
        "Looking busy...",
        "Doing stretches...",
        "Putting on thinking mask...",
        "Running diagnostics...",
        "Preparing witty comeback...",
        "Calculating trajectories...",
        "Donning thinking cape...",
    ]

    def __init__(self, console: Console):
        self.console = console
        self.spinner = None
        self.rotation_task: Optional[asyncio.Task] = None

    def _get_thinking_message(self) -> str:
        """Get a random thinking message."""
        return random.choice(self._THINKING_MESSAGES)

    async def _rotate_messages(self, style: str, interval: float = 5.0):
        """Rotate thinking messages at specified interval."""
        while True:
            try:
                await asyncio.sleep(interval)
                if self.spinner:
                    message = self._get_thinking_message()
                    formatted_message = style.format(message)
                    self.spinner.update(formatted_message)
            except asyncio.CancelledError:
                break
            except Exception:
                break

    def start(self, message: str = "", style: str = None):
        """Start the spinner with a message."""
        if self.spinner:
            # Spinner already running, just update the message
            if message == "":
                message = self._get_thinking_message()
            if style:
                formatted_message = style.format(message)
            else:
                formatted_message = message
            self.spinner.update(formatted_message)
            return

        if message == "":
            message = self._get_thinking_message()
        if style:
            formatted_message = style.format(message)
        else:
            formatted_message = message

        self.spinner = self.console.status(formatted_message, spinner="dots")
        self.spinner.start()

        if self.rotation_task:
            self.rotation_task.cancel()
        if style:
            self.rotation_task = asyncio.create_task(self._rotate_messages(style))

    def stop(self):
        """Stop the spinner."""
        if self.spinner:
            self.spinner.stop()
            self.spinner = None

        if self.rotation_task:
            self.rotation_task.cancel()
            self.rotation_task = None
