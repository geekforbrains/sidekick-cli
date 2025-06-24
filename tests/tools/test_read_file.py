"""Tests for read_file tool."""

import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from sidekick.tools.read_file import read_file


@pytest.mark.asyncio
async def test_read_file_success():
    """Test successful file read."""
    file_content = "Hello, World!\nThis is a test file.\nGoodbye!"

    with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
        result = await read_file("/test/file.txt")

        # Verify the file was opened for reading
        mock_file.assert_called_once_with("/test/file.txt", "r", encoding="utf-8")

        assert result == file_content


@pytest.mark.asyncio
async def test_read_file_not_found():
    """Test error message when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        result = await read_file("/nonexistent/file.txt")

        assert result == "Error: File not found: /nonexistent/file.txt"


@pytest.mark.asyncio
async def test_read_file_permission_denied():
    """Test error message on permission denied."""
    with patch("builtins.open", side_effect=PermissionError("Access denied")):
        result = await read_file("/restricted/file.txt")

        assert result == "Error: Permission denied: /restricted/file.txt"


@pytest.mark.asyncio
async def test_read_file_generic_error():
    """Test error message on generic error."""
    with patch("builtins.open", side_effect=IOError("Disk error")):
        result = await read_file("/test/file.txt")

        assert result == "Error reading file /test/file.txt: Disk error"


@pytest.mark.asyncio
async def test_read_file_with_real_file():
    """Integration test with actual file operations."""
    test_content = "Line 1\nLine 2\nLine 3\n"

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write(test_content)
        tmp_path = tmp.name

    try:
        # Test successful read
        result = await read_file(tmp_path)
        assert result == test_content

    finally:
        # Clean up
        Path(tmp_path).unlink()


@pytest.mark.asyncio
async def test_read_file_nonexistent_real_file():
    """Integration test with non-existent file."""
    nonexistent_path = "/tmp/this_file_definitely_does_not_exist_12345.txt"

    result = await read_file(nonexistent_path)
    assert result == f"Error: File not found: {nonexistent_path}"


@pytest.mark.asyncio
async def test_read_file_empty_file():
    """Test reading an empty file."""
    with patch("builtins.open", mock_open(read_data="")):
        result = await read_file("/test/empty.txt")

        assert result == ""


@pytest.mark.asyncio
async def test_read_file_preserves_encoding():
    """Test that UTF-8 encoding is properly handled."""
    content_with_unicode = "Hello 世界!\nThis file contains émojis 🎉\nGoodbye!"

    with patch("builtins.open", mock_open(read_data=content_with_unicode)) as mock_file:
        result = await read_file("/test/unicode.txt")

        # Verify encoding was specified
        mock_file.assert_called_once_with("/test/unicode.txt", "r", encoding="utf-8")

        assert result == content_with_unicode


@pytest.mark.asyncio
async def test_read_file_large_content():
    """Test reading a large file."""
    large_content = "x" * 10000 + "\n" + "y" * 10000

    with patch("builtins.open", mock_open(read_data=large_content)):
        result = await read_file("/test/large.txt")

        assert result == large_content
        assert len(result) == 20001  # 10000 x's + 1 newline + 10000 y's
