import asyncio
import logging
import os
import signal
import subprocess
import sys

from sidekick import ui
from sidekick.agent import process_request
from sidekick.commands import handle_command
from sidekick.mcp import load_mcp_servers
from sidekick.messages import MessageHistory
from sidekick.session import session
from sidekick.usage import usage_tracker
from sidekick.utils.error import ErrorContext
from sidekick.utils.input import create_multiline_prompt_session, get_multiline_input

log = logging.getLogger(__name__)


def _restore_default_signal_handler():
    """Restore the default SIGINT handler."""
    signal.signal(signal.SIGINT, signal.default_int_handler)


def _should_exit(user_input: str) -> bool:
    """Check if user wants to exit."""
    return user_input.lower() in ["exit", "quit"]


async def _display_server_info():
    """Display information about configured MCP servers."""
    servers = load_mcp_servers()
    ui.info("Starting MCP servers")
    if servers:
        for server in servers:
            ui.bullet(server.display_name)
    else:
        ui.bullet("No servers configured")


class Repl:
    """Manages the application's Read-Eval-Print Loop and interrupt handling."""

    def __init__(self, project_guide=None):
        """Initializes the REPL manager with signal handler."""
        self.loop = asyncio.get_event_loop()
        self.current_task = None
        self.signal_handler = self._setup_signal_handler()
        self.message_history = MessageHistory()
        if project_guide:
            self.message_history.set_project_guide(project_guide)

    def _kill_child_processes(self):
        """Kill all child processes of the current process."""
        if sys.platform == "win32":
            return

        pid = os.getpid()
        try:
            import psutil

            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                try:
                    child.kill()
                except Exception:
                    pass
        except ImportError:
            try:
                subprocess.run(["pkill", "-P", str(pid)], capture_output=True)
            except Exception:
                pass

    def _setup_signal_handler(self):
        """Set up SIGINT handler for immediate cancellation."""

        def signal_handler(signum, frame):
            if self.current_task and not self.current_task.done():
                ui.stop_spinner()
                self._kill_child_processes()
                self.loop.call_soon_threadsafe(self.current_task.cancel)
            else:
                raise KeyboardInterrupt()

        signal.signal(signal.SIGINT, signal_handler)
        return signal_handler

    async def _handle_user_request(self, user_input: str):
        """Process a user request with proper exception handling."""
        log.debug(f"Handling user request: {user_input.replace('\n', ' ')[:100]}...")
        ui.start_spinner()

        request_task = asyncio.create_task(process_request(user_input, self.message_history))
        self.current_task = request_task

        ctx = ErrorContext("request", ui)

        try:
            resp = await request_task
            ui.stop_spinner()
            if resp:
                has_footer = bool(usage_tracker.last_request)
                ui.agent(resp, has_footer=has_footer)
                if usage_tracker.last_request:
                    ui.usage(usage_tracker.last_request)
        except asyncio.CancelledError:
            ui.stop_spinner()
            ui.warning("Request interrupted")
        except Exception as e:
            await ctx.handle(e)
        finally:
            self.current_task = None

    async def run(self):
        """Runs the main read-eval-print loop."""
        ui.info(f"Using model {session.current_model}")
        await _display_server_info()

        ui.success("Go kick some ass!")
        prompt_session = create_multiline_prompt_session()

        while True:
            ui.line()

            try:
                user_input = await get_multiline_input(prompt_session)
            except EOFError:
                break
            except KeyboardInterrupt:
                ui.muted("Use Ctrl+D or 'exit' to quit")
                continue

            ui.line()
            ui.reset_output_context()

            if not user_input:
                continue

            if _should_exit(user_input):
                break

            if await handle_command(user_input, self.message_history):
                continue

            await self._handle_user_request(user_input)

        _restore_default_signal_handler()
        ui.info("Thanks for all the fish.")
