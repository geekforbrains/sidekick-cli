import asyncio
import logging
import signal

from sidekick import ui
from sidekick.agent import get_or_create_agent, process_request
from sidekick.commands import handle_command
from sidekick.mcp import load_mcp_servers
from sidekick.session import session
from sidekick.utils.error import ErrorContext
from sidekick.utils.input import create_multiline_prompt_session, get_multiline_input

log = logging.getLogger(__name__)


def _setup_signal_handler(loop):
    """Set up SIGINT handler for graceful cancellation."""

    def signal_handler(signum, frame):
        session.sigint_received = True
        if session.current_task and not session.current_task.done():
            loop.call_soon_threadsafe(session.current_task.cancel)
        else:
            raise KeyboardInterrupt()

    signal.signal(signal.SIGINT, signal_handler)
    return signal_handler


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
    """Manages the application's Read-Eval-Print Loop and session state."""

    def __init__(self):
        """Initializes the REPL manager with an agent and signal handler."""
        self.mcp_agent = get_or_create_agent()
        self.loop = asyncio.get_event_loop()
        self.signal_handler = _setup_signal_handler(self.loop)

    async def _handle_user_request(self, user_input: str):
        """Process a user request with proper exception handling."""
        log.debug(f"Handling user request: {user_input.replace('\n', ' ')[:100]}...")
        ui.start_spinner(ui.get_thinking_message())
        session.sigint_received = False

        request_task = asyncio.create_task(process_request(user_input))
        session.current_task = request_task

        async def recreate_agent():
            if session.current_model in session.agents:
                if self.mcp_agent._mcp_entered:
                    await self.mcp_agent.__aexit__(None, None, None)
                del session.agents[session.current_model]
                self.mcp_agent = get_or_create_agent()
                await self.mcp_agent.__aenter__()

        ctx = ErrorContext("request", ui)

        try:
            resp = await request_task
            ui.stop_spinner()
            if resp:
                has_footer = bool(session.last_usage)
                ui.agent(resp, has_footer=has_footer)
                if session.last_usage:
                    ui.usage(session.last_usage)
        except asyncio.CancelledError as e:
            ctx.add_cleanup(recreate_agent)
            await ctx.handle(e)
        except KeyboardInterrupt:
            ui.stop_spinner()
            if not request_task.done():
                request_task.cancel()
                try:
                    await request_task
                except asyncio.CancelledError:
                    pass
            ui.warning("Request interrupted")
        except Exception as e:
            await ctx.handle(e)
        finally:
            session.current_task = None

    async def _handle_model_switch(self):
        """Handles switching the active model and reconnecting servers."""
        ui.start_spinner("Switching model...", ui.SpinnerStyle.MUTED)
        try:
            if self.mcp_agent._mcp_entered:
                await self.mcp_agent.__aexit__(None, None, None)

            self.mcp_agent = get_or_create_agent()
            await self.mcp_agent.__aenter__()
            session.model_switched = False
        finally:
            ui.stop_spinner()

    async def run(self):
        """Runs the main read-eval-print loop."""
        ui.info(f"Using model {session.current_model}")
        await _display_server_info()

        ui.start_spinner("Initializing servers...", ui.SpinnerStyle.MUTED)
        async with self.mcp_agent:
            ui.stop_spinner()
            ui.success("Go kick some ass!")
            prompt_session = create_multiline_prompt_session()

            while True:
                ui.line()

                try:
                    user_input = await get_multiline_input(prompt_session)
                except (EOFError, KeyboardInterrupt):
                    break

                ui.line()
                ui.reset_output_context()

                if not user_input:
                    continue

                if _should_exit(user_input):
                    break

                if await handle_command(user_input):
                    if session.model_switched:
                        await self._handle_model_switch()
                    continue

                await self._handle_user_request(user_input)
                signal.signal(signal.SIGINT, self.signal_handler)

        _restore_default_signal_handler()
        ui.info("Thanks for all the fish.")
