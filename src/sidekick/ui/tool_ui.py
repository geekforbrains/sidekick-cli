"""
Tool confirmation UI components, separated from business logic.
"""

from sidekick.configuration.settings import ApplicationSettings
from sidekick.constants import APP_NAME, TOOL_UPDATE_FILE, TOOL_WRITE_FILE
from sidekick.core.tool_handler import ToolConfirmationRequest, ToolConfirmationResponse
from sidekick.types import ToolArgs
from sidekick.ui import console as ui
from sidekick.utils.helpers import ext_to_lang, key_to_title, render_file_diff


class ToolUI:
    """Handles tool confirmation UI presentation."""

    def __init__(self):
        pass

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

    def _create_code_block(self, filepath: str, content: str):
        """
        Create a code block for the given file path and content.

        Args:
            filepath: The path to the file.
            content: The content of the file.

        Returns:
            Markdown: A Markdown object representing the code block.
        """
        lang = ext_to_lang(filepath)
        code_block = f"```{lang}\n{content}\n```"
        return ui.markdown(code_block)

    def _render_args(self, tool_name: str, args: ToolArgs) -> str:
        """
        Render the tool arguments for display.

        Args:
            tool_name: Name of the tool.
            args: Tool arguments.

        Returns:
            str: Formatted arguments for display.
        """
        # Show diff between `target` and `patch` on file updates
        if tool_name == TOOL_UPDATE_FILE:
            return render_file_diff(args["target"], args["patch"], ui.colors)

        # Show file content on write_file
        elif tool_name == TOOL_WRITE_FILE:
            return self._create_code_block(args["filepath"], args["content"])

        # Default to showing key and value on new line
        content = ""
        for key, value in args.items():
            if isinstance(value, list):
                content += f"{key_to_title(key)}:\n"
                for item in value:
                    content += f"  - {item}\n"
                content += "\n"
            else:
                # If string length is over 200 characters, split to new line
                value = str(value)
                content += f"{key_to_title(key)}:"
                if len(value) > 200:
                    content += f"\n{value}\n\n"
                else:
                    content += f" {value}\n\n"
        return content.strip()

    async def show_confirmation(
        self, request: ToolConfirmationRequest, state_manager=None
    ) -> ToolConfirmationResponse:
        """
        Show tool confirmation UI and get user response.

        Args:
            request: The confirmation request.

        Returns:
            ToolConfirmationResponse: User's response to the confirmation.
        """
        title = self._get_tool_title(request.tool_name)
        content = self._render_args(request.tool_name, request.args)

        await ui.tool_confirm(title, content, filepath=request.filepath)

        # If tool call has filepath, show it under panel
        if request.filepath:
            await ui.usage(f"File: {request.filepath}")

        await ui.print("  1. Yes (default)")
        await ui.print("  2. Yes, and don't ask again for commands like this")
        await ui.print(f"  3. No, and tell {APP_NAME} what to do differently")
        resp = (
            await ui.input(
                session_key="tool_confirm",
                pretext="  Choose an option [1/2/3]: ",
                state_manager=state_manager,
            )
            or "1"
        )

        if resp == "2":
            return ToolConfirmationResponse(approved=True, skip_future=True)
        elif resp == "3":
            return ToolConfirmationResponse(approved=False, abort=True)
        else:
            return ToolConfirmationResponse(approved=True)

    def show_sync_confirmation(self, request: ToolConfirmationRequest) -> ToolConfirmationResponse:
        """
        Show tool confirmation UI synchronously and get user response.

        Args:
            request: The confirmation request.

        Returns:
            ToolConfirmationResponse: User's response to the confirmation.
        """
        title = self._get_tool_title(request.tool_name)
        content = self._render_args(request.tool_name, request.args)

        # Display styled confirmation panel using sync UI functions
        ui.sync_tool_confirm(title, content)
        if request.filepath:
            ui.sync_print(f"File: {request.filepath}", style=ui.colors.muted)

        ui.sync_print("  1. Yes (default)")
        ui.sync_print("  2. Yes, and don't ask again for commands like this")
        ui.sync_print(f"  3. No, and tell {APP_NAME} what to do differently")
        resp = input("  Choose an option [1/2/3]: ").strip() or "1"

        if resp == "2":
            return ToolConfirmationResponse(approved=True, skip_future=True)
        elif resp == "3":
            return ToolConfirmationResponse(approved=False, abort=True)
        else:
            return ToolConfirmationResponse(approved=True)

    async def log_mcp(self, title: str, args: ToolArgs):
        """
        Display MCP tool with its arguments.

        Args:
            title: Title to display.
            args: Arguments to display.
        """
        if not args:
            return

        await ui.info(title)
        for key, value in args.items():
            if isinstance(value, list):
                value = ", ".join(value)
            await ui.muted(f"{key}: {value}", spaces=4)
