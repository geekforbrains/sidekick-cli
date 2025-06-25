"""Command handler routing tests (DRY parametrised)."""

from unittest.mock import AsyncMock

import pytest

from sidekick.commands import handle_command


@pytest.mark.parametrize(
    "user_input, patch_target, expected_args",
    [
        ("/dump", "handle_dump", []),
        ("/yolo", "handle_yolo", []),
        ("/model 2", "handle_model", ["2"]),
    ],
)
@pytest.mark.asyncio
async def test_handle_command_routes(monkeypatch, user_input, patch_target, expected_args):
    mock_func = AsyncMock()
    monkeypatch.setattr(f"sidekick.commands.{patch_target}", mock_func)

    result = await handle_command(user_input)

    assert result is True

    # Verify called arguments irrespective of list vs positional nuance
    call_args = mock_func.call_args[0]
    if expected_args:
        assert call_args[0] == expected_args
    else:
        # No arguments expected
        assert call_args == ()


@pytest.mark.asyncio
async def test_handle_command_non_command():
    """Input without leading slash should not be treated as command."""
    assert await handle_command("not a command") is False


@pytest.mark.asyncio
async def test_handle_command_unknown():
    """Unknown command string should return False."""
    assert await handle_command("/unknown") is False
