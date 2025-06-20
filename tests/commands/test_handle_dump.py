"""Test /dump command handler."""

from unittest.mock import patch

import pytest

from sidekick.commands import handle_dump


@pytest.mark.asyncio
async def test_handle_dump(mock_ui, mock_session):
    """Test /dump command shows message history."""
    mock_session.messages = ["msg1", "msg2"]

    with patch("sidekick.commands.ui", mock_ui), patch("sidekick.commands.session", mock_session):
        await handle_dump()
        mock_ui.dump.assert_called_once_with(["msg1", "msg2"])
