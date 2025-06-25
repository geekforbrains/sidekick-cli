"""Tests for read_file tool – refactored to eliminate duplication."""

from unittest.mock import mock_open, patch

import pytest

from sidekick.tools.read_file import read_file

# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_file_success():
    content = "Hello, World!\nThis is a test file."
    with patch("builtins.open", mock_open(read_data=content)) as m:
        assert await read_file("/test/file.txt") == content
        m.assert_called_once_with("/test/file.txt", "r", encoding="utf-8")


# ---------------------------------------------------------------------------
# Error scenarios – parametrised to avoid repetition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "side_effect, expected",
    [
        (FileNotFoundError(), "Error: File not found: /x"),
        (PermissionError("Access denied"), "Error: Permission denied: /x"),
        (IOError("Disk error"), "Error reading file /x: Disk error"),
    ],
)
@pytest.mark.asyncio
async def test_read_file_errors(side_effect, expected):
    with patch("builtins.open", side_effect=side_effect):
        assert await read_file("/x") == expected


# ---------------------------------------------------------------------------
# Integration-style tests with real temp file
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_read_file_real_file(tmp_path):
    tmp_file = tmp_path / "sample.txt"
    tmp_file.write_text("Line1\nLine2")
    assert await read_file(str(tmp_file)) == "Line1\nLine2"


@pytest.mark.asyncio
async def test_read_file_empty_file():
    with patch("builtins.open", mock_open(read_data="")):
        assert await read_file("/empty.txt") == ""


@pytest.mark.asyncio
async def test_read_file_large_content():
    large_content = "x" * 10000 + "\n" + "y" * 10000
    with patch("builtins.open", mock_open(read_data=large_content)):
        result = await read_file("/big.txt")
        assert result == large_content and len(result) == 20001
