"""Test /dump command handler."""

from unittest.mock import Mock, patch

import pytest

from sidekick.commands import handle_dump


@pytest.mark.asyncio
async def test_handle_dump_writes_to_file_and_pretty_prints(mock_ui, tmp_path):
    """Test /dump command writes message history to dump.log and pretty prints it."""
    temp_dump_file = tmp_path / "dump.log"

    mock_message_history = Mock()
    mock_message_history.__iter__ = Mock(
        return_value=iter(
            [
                {"role": "user", "content": "hello"},
                {"role": "agent", "content": "hi"},
            ]
        )
    )

    with (
        patch("sidekick.commands.dump.ui", mock_ui),
        patch("sidekick.commands.dump.DUMP_FILE_PATH", str(temp_dump_file)),
    ):
        await handle_dump(mock_message_history)

        mock_ui.success.assert_called_once_with(f"Message history dumped to {temp_dump_file}")

        assert temp_dump_file.exists()
        content = temp_dump_file.read_text()

        assert "Message #0 - Type: dict" in content
        assert "Message #1 - Type: dict" in content
        assert "'role': 'user'" in content
        assert "'content': 'hello'" in content
        assert "'role': 'agent'" in content
        assert "'content': 'hi'" in content
        assert "=" * 80 in content
