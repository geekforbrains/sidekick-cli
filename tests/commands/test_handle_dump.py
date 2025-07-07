"""Test /dump command handler."""

import json
from unittest.mock import patch

import pytest

from sidekick.commands import handle_dump


@pytest.mark.asyncio
async def test_handle_dump_writes_to_file_and_pretty_prints(mock_ui, mock_session, tmp_path):
    """Test /dump command writes message history to dump.log and pretty prints it."""
    temp_dump_file = tmp_path / "dump.log"

    mock_session.messages = [
        {"role": "user", "content": "hello"},
        {"role": "agent", "content": "hi"},
    ]

    with (
        patch("sidekick.commands.ui", mock_ui),
        patch("sidekick.commands.session", mock_session),
        patch("sidekick.commands.DUMP_FILE_PATH", str(temp_dump_file)),
    ):
        await handle_dump()

        mock_ui.success.assert_called_once_with(f"Message history dumped to {temp_dump_file}")

        assert temp_dump_file.exists()
        content = temp_dump_file.read_text()
        expected_content = json.dumps(mock_session.messages, indent=2)
        assert content == expected_content
