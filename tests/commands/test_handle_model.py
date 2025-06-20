"""Test /model command handler."""

from unittest.mock import MagicMock, patch

import pytest

from sidekick.commands import handle_model


@pytest.mark.asyncio
async def test_handle_model_list(mock_ui, mock_session, mock_models):
    """Test /model with no args lists available models."""
    mock_session.current_model = "model2"

    with (
        patch("sidekick.commands.ui", mock_ui),
        patch("sidekick.commands.session", mock_session),
        patch("sidekick.commands.MODELS", mock_models),
    ):
        await handle_model([])

        mock_ui.info.assert_called_with("Available models:")
        calls = mock_ui.bullet.call_args_list
        assert len(calls) == 3
        assert "2. model2 (current)" in str(calls[1])


@pytest.mark.asyncio
async def test_handle_model_switch(mock_ui, mock_session, mock_models):
    """Test /model <num> switches to selected model."""
    mock_session.agents = MagicMock()
    mock_session.model_switched = False

    with (
        patch("sidekick.commands.ui", mock_ui),
        patch("sidekick.commands.session", mock_session),
        patch("sidekick.commands.MODELS", mock_models),
    ):
        await handle_model(["2"])

        assert mock_session.current_model == "model2"
        mock_session.agents.clear.assert_called_once()
        assert mock_session.model_switched is True
        mock_ui.info.assert_called_with("Switched to model: model2")


@pytest.mark.asyncio
async def test_handle_model_invalid_number(mock_ui):
    """Test /model with invalid number shows error."""
    with (
        patch("sidekick.commands.ui", mock_ui),
        patch("sidekick.commands.MODELS", {"model1": {}, "model2": {}}),
    ):
        await handle_model(["5"])
        mock_ui.error.assert_called_with("Invalid model number. Choose between 1 and 2")


@pytest.mark.asyncio
async def test_handle_model_set_default(mock_ui):
    """Test /model <num> default sets default model in config."""
    mock_update = MagicMock()

    with (
        patch("sidekick.commands.ui", mock_ui),
        patch("sidekick.commands.MODELS", {"model1": {}, "model2": {}}),
        patch("sidekick.commands.update_config_file", mock_update),
    ):
        await handle_model(["2", "default"])

        mock_update.assert_called_once_with({"default_model": "model2"})
        mock_ui.success.assert_called_with("Set model2 as default model")
