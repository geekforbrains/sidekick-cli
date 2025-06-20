"""Test main command handler routing."""

from unittest.mock import AsyncMock, patch

import pytest

from sidekick.commands import handle_command


@pytest.mark.asyncio
async def test_handle_command_routes_dump():
    """Test /dump command is routed correctly."""
    with patch("sidekick.commands.handle_dump", new_callable=AsyncMock) as mock_dump:
        result = await handle_command("/dump")
        assert result is True
        mock_dump.assert_called_once()


@pytest.mark.asyncio
async def test_handle_command_routes_yolo():
    """Test /yolo command is routed correctly."""
    with patch("sidekick.commands.handle_yolo", new_callable=AsyncMock) as mock_yolo:
        result = await handle_command("/yolo")
        assert result is True
        mock_yolo.assert_called_once()


@pytest.mark.asyncio
async def test_handle_command_routes_model():
    """Test /model command is routed correctly."""
    with patch("sidekick.commands.handle_model", new_callable=AsyncMock) as mock_model:
        result = await handle_command("/model 2")
        assert result is True
        mock_model.assert_called_once_with(["2"])


@pytest.mark.asyncio
async def test_handle_command_non_command():
    """Test non-command input returns False."""
    result = await handle_command("not a command")
    assert result is False


@pytest.mark.asyncio
async def test_handle_command_unknown():
    """Test unknown command returns False."""
    result = await handle_command("/unknown")
    assert result is False
