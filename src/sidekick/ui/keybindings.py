"""Key binding handlers for Sidekick UI."""

from prompt_toolkit.key_binding import KeyBindings


def create_key_bindings():
    """Create and configure key bindings for the UI."""
    kb = KeyBindings()

    @kb.add("escape", eager=True)
    def _cancel(event):
        """Kill the running agent task, if any."""
        # Key bindings can't easily access state_manager, so we'll handle this differently
        # This will be handled in the REPL where state is available
        if (
            hasattr(event.app, "current_task")
            and event.app.current_task
            and not event.app.current_task.done()
        ):
            event.app.current_task.cancel()
            event.app.invalidate()

    @kb.add("enter")
    def _submit(event):
        """Submit the current buffer."""
        event.current_buffer.validate_and_handle()

    @kb.add("c-o")  # ctrl+o
    def _newline(event):
        """Insert a newline character."""
        event.current_buffer.insert_text("\n")

    return kb
