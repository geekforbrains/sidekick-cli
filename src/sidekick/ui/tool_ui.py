"""
Tool confirmation UI components, separated from business logic.
"""

from rich.markdown import Markdown as RichMarkdown

from sidekick.configuration import ApplicationSettings
from sidekick.constants import APP_NAME, TOOL_UPDATE_FILE, TOOL_WRITE_FILE
from sidekick.core.tool_handler import ToolConfirmationRequest, ToolConfirmationResponse
from sidekick.types import ToolArgs
from sidekick.ui.input import input
from sidekick.ui.output import info, muted, print, usage
from sidekick.ui.panels import tool_confirm
from sidekick.ui.shared import console, create_padded_panel, theme
from sidekick.utils.diff_utils import render_file_diff
from sidekick.utils.text_utils import ext_to_lang, key_to_title


class ToolUI:
    """Handles tool confirmation UI presentation."""

    def __init__(self):
        self.theme = theme
        self.console = console

    def _get_tool_title(self, tool_name: str) -> str:
        """
        Get the display title for a tool.

        Args:
            tool_name: Name of the tool.

        Returns:
            str: Display title.
        """
        app_settings = ApplicationSettings()
        if tool_name in app_settings.internal_tools:
            return f"Tool({tool_name})"
        else:
            return f"MCP({tool_name})"

    def _create_code_block(self, filepath: str, content: str) -> RichMarkdown:
        """
        Create a code block for the given file path and content.

        Args:
            filepath: The path to the file.
            content: The content of the file.

        Returns:
            RichMarkdown: A Markdown object representing the code block.
        """
        lang = ext_to_lang(filepath)
        code_block = f"```{lang}\n{content}\n```"
        return RichMarkdown(code_block)

    def _render_args(self, tool_name: str, args: ToolArgs) -> str:
        """
        Render the tool arguments for display.

        Args:
            tool_name: Name of the tool.
            args: Tool arguments.

        Returns:
            str: Formatted arguments for display.
        """
        if tool_name == TOOL_UPDATE_FILE:
            return render_file_diff(args["target"], args["patch"], self.theme.colors)

        elif tool_name == TOOL_WRITE_FILE:
            return self._create_code_block(args["filepath"], args["content"])

        content = ""
        for key, value in args.items():
            if isinstance(value, list):
                content += f"{key_to_title(key)}:\n"
                for item in value:
                    content += f"  - {item}\n"
                content += "\n"
            else:
                value = str(value)
                content += f"{key_to_title(key)}:"
                if len(value) > 200:
                    content += f"\n{value}\n\n"
                else:
                    content += f" {value}\n\n"
        return content.strip()

    async def show_confirmation(
        self, request: ToolConfirmationRequest, session=None
    ) -> ToolConfirmationResponse:
        """
        Show tool confirmation UI and get user response.

        Args:
            request: The confirmation request.
            session: Session for async input.

        Returns:
            ToolConfirmationResponse: User's response to the confirmation.
        """
        return await self._show_confirmation_common(request, is_async=True, session=session)

    def show_sync_confirmation(self, request: ToolConfirmationRequest) -> ToolConfirmationResponse:
        """
        Show tool confirmation UI synchronously and get user response.

        Args:
            request: The confirmation request.

        Returns:
            ToolConfirmationResponse: User's response to the confirmation.
        """
        import asyncio

        return asyncio.run(self._show_confirmation_common(request, is_async=False))

    async def _show_confirmation_common(
        self, request: ToolConfirmationRequest, is_async: bool = True, session=None
    ) -> ToolConfirmationResponse:
        """
        Common confirmation logic for both async and sync modes.

        Args:
            request: The confirmation request.
            is_async: Whether to use async UI components.
            session: Session for async input.

        Returns:
            ToolConfirmationResponse: User's response to the confirmation.
        """
        title = self._get_tool_title(request.tool_name)
        content = self._render_args(request.tool_name, request.args)

        # Display confirmation panel
        if is_async:
            await tool_confirm(title, content, filepath=request.filepath)
            if request.filepath:
                await usage(f"File: {request.filepath}")
        else:
            bottom_padding = 0 if request.filepath else 1
            panel_obj = create_padded_panel(
                title, content, border_style=self.theme.warning, padding_bottom=bottom_padding
            )
            self.console.print(panel_obj)
            if request.filepath:
                self.console.print(f"File: {request.filepath}", style=self.theme.muted)

        # Display options
        options = [
            "  1. Yes (default)",
            "  2. Yes, and don't ask again for commands like this",
            f"  3. No, and tell {APP_NAME} what to do differently",
        ]

        if is_async:
            for option in options:
                await print(option)
            resp = (
                await input(
                    session_key="tool_confirm",
                    pretext="  Choose an option [1/2/3]: ",
                    session=session,
                )
                or "1"
            )
        else:
            for option in options:
                self.console.print(option)
            resp = input("  Choose an option [1/2/3]: ").strip() or "1"
            print()

        # Process response
        if resp == "2":
            return ToolConfirmationResponse(approved=True, skip_future=True)
        elif resp == "3":
            return ToolConfirmationResponse(approved=False, abort=True)
        else:
            return ToolConfirmationResponse(approved=True)

    async def log_mcp(self, title: str, args: ToolArgs) -> None:
        """
        Display MCP tool with its arguments.

        Args:
            title: Title to display.
            args: Arguments to display.
        """
        if not args:
            return

        await info(title)
        for key, value in args.items():
            if isinstance(value, list):
                value = ", ".join(value)
            await muted(f"{key}: {value}", spaces=4)
