"""Test /dump command handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sidekick.commands import handle_dump


@pytest.mark.asyncio
async def test_handle_dump():
    """Test /dump command shows message history."""
    mock_ui = AsyncMock()
    mock_session = MagicMock()
    mock_session.messages = ["msg1", "msg2"]

    with patch("sidekick.commands.ui", mock_ui), patch("sidekick.commands.session", mock_session):
        await handle_dump()
        mock_ui.dump.assert_called_once_with(["msg1", "msg2"])
