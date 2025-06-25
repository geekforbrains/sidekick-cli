"""Tests for read_file tool."""

from unittest.mock import MagicMock, mock_open, patch

import pytest
from pydantic_ai import RunContext

from sidekick.deps import ToolDeps
from sidekick.tools.read_file import read_file


@pytest.fixture
def mock_context():
    """Create a mock RunContext with ToolDeps."""
    mock_deps = MagicMock(spec=ToolDeps)
    mock_deps.display_tool_status = None
    mock_ctx = MagicMock(spec=RunContext)
    mock_ctx.deps = mock_deps
    return mock_ctx


@pytest.mark.asyncio
async def test_read_file_success(mock_context):
    content = "Hello, World!\nThis is a test file."
    with patch("builtins.open", mock_open(read_data=content)) as m:
        assert await read_file(mock_context, "/test/file.txt") == content
        m.assert_called_once_with("/test/file.txt", "r", encoding="utf-8")


@pytest.mark.parametrize(
    "side_effect, expected",
    [
        (FileNotFoundError(), "Error: File not found: /x"),
        (PermissionError("Access denied"), "Error: Permission denied: /x"),
        (IOError("Disk error"), "Error reading file /x: Disk error"),
    ],
)
@pytest.mark.asyncio
async def test_read_file_errors(side_effect, expected, mock_context):
    with patch("builtins.open", side_effect=side_effect):
        assert await read_file(mock_context, "/x") == expected


@pytest.mark.asyncio
async def test_read_file_real_file(tmp_path, mock_context):
    tmp_file = tmp_path / "sample.txt"
    tmp_file.write_text("Line1\nLine2")
    assert await read_file(mock_context, str(tmp_file)) == "Line1\nLine2"


@pytest.mark.asyncio
async def test_read_file_empty_file(mock_context):
    with patch("builtins.open", mock_open(read_data="")):
        assert await read_file(mock_context, "/empty.txt") == ""


@pytest.mark.asyncio
async def test_read_file_large_content(mock_context):
    large_content = "x" * 10000 + "\n" + "y" * 10000
    with patch("builtins.open", mock_open(read_data=large_content)):
        result = await read_file(mock_context, "/big.txt")
        assert result == large_content and len(result) == 20001
