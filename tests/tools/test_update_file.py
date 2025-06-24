"""Tests for update_file tool."""

import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from pydantic_ai import ModelRetry

from sidekick.tools.update_file import update_file


@pytest.mark.asyncio
async def test_update_file_success():
    """Test successful file update."""
    original_content = "Hello, World!\nThis is a test file.\nGoodbye!"
    old_content = "This is a test file."
    new_content = "This is an updated file."
    expected_content = "Hello, World!\nThis is an updated file.\nGoodbye!"

    with patch("builtins.open", mock_open(read_data=original_content)) as mock_file:
        result = await update_file("/test/file.txt", old_content, new_content)

        # Verify the file was opened for reading and writing
        assert mock_file.call_count == 2
        mock_file.assert_any_call("/test/file.txt", "r", encoding="utf-8")
        mock_file.assert_any_call("/test/file.txt", "w", encoding="utf-8")

        # Verify the updated content was written
        handle = mock_file()
        handle.write.assert_called_once_with(expected_content)

        assert result == "Successfully updated /test/file.txt"


@pytest.mark.asyncio
async def test_update_file_content_not_found():
    """Test ModelRetry when content to replace is not found."""
    original_content = "Hello, World!\nThis is a test file.\nGoodbye!"
    old_content = "This content does not exist"
    new_content = "This is an updated file."

    with patch("builtins.open", mock_open(read_data=original_content)):
        with pytest.raises(ModelRetry) as exc_info:
            await update_file("/test/file.txt", old_content, new_content)

        error_msg = str(exc_info.value)
        assert "Content to replace not found in /test/file.txt" in error_msg
        assert "Searched for: 'This content does not exist'" in error_msg
        assert "re-read the file" in error_msg


@pytest.mark.asyncio
async def test_update_file_content_not_found_long_content():
    """Test ModelRetry with truncated preview for long content."""
    original_content = "Short content"
    old_content = "a" * 150  # Long content that doesn't exist
    new_content = "New content"

    with patch("builtins.open", mock_open(read_data=original_content)):
        with pytest.raises(ModelRetry) as exc_info:
            await update_file("/test/file.txt", old_content, new_content)

        error_msg = str(exc_info.value)
        assert "Content to replace not found" in error_msg
        # Check that long content is truncated
        assert f"Searched for: '{'a' * 100}...'" in error_msg


@pytest.mark.asyncio
async def test_update_file_not_found():
    """Test ModelRetry when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(ModelRetry) as exc_info:
            await update_file("/nonexistent/file.txt", "old", "new")

        error_msg = str(exc_info.value)
        assert "File not found: /nonexistent/file.txt" in error_msg
        assert "check the file path" in error_msg


@pytest.mark.asyncio
async def test_update_file_read_error():
    """Test ModelRetry on generic read error."""
    with patch("builtins.open", side_effect=PermissionError("Access denied")):
        with pytest.raises(ModelRetry) as exc_info:
            await update_file("/test/file.txt", "old", "new")

        error_msg = str(exc_info.value)
        assert "Error reading file /test/file.txt" in error_msg
        assert "Access denied" in error_msg


@pytest.mark.asyncio
async def test_update_file_write_error():
    """Test ModelRetry on write error."""
    original_content = "Hello, World!\nThis is a test file.\nGoodbye!"
    old_content = "This is a test file."
    new_content = "This is an updated file."

    # Mock successful read but failed write
    read_mock = mock_open(read_data=original_content)

    def open_side_effect(filepath, mode, encoding="utf-8"):
        if mode == "r":
            return read_mock(filepath, mode, encoding)
        else:  # mode == "w"
            raise PermissionError("Cannot write to file")

    with patch("builtins.open", side_effect=open_side_effect):
        with pytest.raises(ModelRetry) as exc_info:
            await update_file("/test/file.txt", old_content, new_content)

        error_msg = str(exc_info.value)
        assert "Error writing to file /test/file.txt" in error_msg
        assert "Cannot write to file" in error_msg


@pytest.mark.asyncio
async def test_update_file_with_real_file():
    """Integration test with actual file operations."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write("Line 1\nLine 2\nLine 3\n")
        tmp_path = tmp.name

    try:
        # Test successful update
        result = await update_file(tmp_path, "Line 2", "Updated Line 2")
        assert result == f"Successfully updated {tmp_path}"

        # Verify content was updated
        with open(tmp_path, "r") as f:
            content = f.read()
        assert content == "Line 1\nUpdated Line 2\nLine 3\n"

        # Test content not found
        with pytest.raises(ModelRetry) as exc_info:
            await update_file(tmp_path, "Non-existent line", "New line")
        assert "Content to replace not found" in str(exc_info.value)

    finally:
        # Clean up
        Path(tmp_path).unlink()


@pytest.mark.asyncio
async def test_update_file_only_first_occurrence():
    """Test that only the first occurrence is replaced."""
    original_content = "foo\nbar\nfoo\nbaz"
    old_content = "foo"
    new_content = "replaced"
    expected_content = "replaced\nbar\nfoo\nbaz"

    with patch("builtins.open", mock_open(read_data=original_content)) as mock_file:
        result = await update_file("/test/file.txt", old_content, new_content)

        # Verify only first occurrence was replaced
        handle = mock_file()
        handle.write.assert_called_once_with(expected_content)

        assert result == "Successfully updated /test/file.txt"


@pytest.mark.asyncio
async def test_update_file_preserves_encoding():
    """Test that UTF-8 encoding is properly handled."""
    original_content = "Hello 世界!\nThis is a test file with émojis 🎉\nGoodbye!"
    old_content = "This is a test file with émojis 🎉"
    new_content = "This is an updated file with émojis 🎊"
    expected_content = "Hello 世界!\nThis is an updated file with émojis 🎊\nGoodbye!"

    with patch("builtins.open", mock_open(read_data=original_content)) as mock_file:
        result = await update_file("/test/file.txt", old_content, new_content)

        # Verify encoding was specified
        mock_file.assert_any_call("/test/file.txt", "r", encoding="utf-8")
        mock_file.assert_any_call("/test/file.txt", "w", encoding="utf-8")

        # Verify the content was correctly updated
        handle = mock_file()
        handle.write.assert_called_once_with(expected_content)

        assert result == "Successfully updated /test/file.txt"
