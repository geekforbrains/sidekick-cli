"""Test /yolo command handler."""

from unittest.mock import patch

import pytest

from sidekick.commands import handle_yolo


@pytest.mark.asyncio
async def test_handle_yolo_disables_confirmation(mock_ui, mock_session):
    """Test /yolo toggles confirmation from enabled to disabled."""
    mock_session.confirmation_enabled = True

    with (
        patch("sidekick.commands.yolo.ui", mock_ui),
        patch("sidekick.commands.yolo.session", mock_session),
    ):
        await handle_yolo()
        assert mock_session.confirmation_enabled is False
        mock_ui.info.assert_called_with("Tool confirmations disabled (YOLO mode)")


@pytest.mark.asyncio
async def test_handle_yolo_enables_confirmation(mock_ui, mock_session):
    """Test /yolo toggles confirmation from disabled to enabled."""
    mock_session.confirmation_enabled = False

    with (
        patch("sidekick.commands.yolo.ui", mock_ui),
        patch("sidekick.commands.yolo.session", mock_session),
    ):
        await handle_yolo()
        assert mock_session.confirmation_enabled is True
        mock_ui.info.assert_called_with("Tool confirmations enabled")
