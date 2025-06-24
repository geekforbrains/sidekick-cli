"""Tests for the search tool."""

from unittest.mock import AsyncMock, patch

import pytest

from sidekick.tools.search import search_content, search_dirs, search_files


# A mocked successful process with some output
def create_mock_process(stdout, stderr="", returncode=0):
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(return_value=(stdout.encode(), stderr.encode()))
    mock_process.returncode = returncode
    return mock_process


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_search_files_success(mock_subprocess_exec):
    """Test successful file search."""
    mock_subprocess_exec.return_value = create_mock_process("./src/main.py\n./src/agent.py")

    result = await search_files("*.py")

    assert mock_subprocess_exec.call_count == 1
    # Check that the core arguments are correct
    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "find"
    assert "-type" in args
    assert "f" in args
    assert "-name" in args
    assert "*.py" in args

    assert result == "./src/main.py\n./src/agent.py"


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_search_dirs_success(mock_subprocess_exec):
    """Test successful directory search."""
    mock_subprocess_exec.return_value = create_mock_process("./src/utils\n./tests/tools")

    result = await search_dirs("*tools*")

    assert mock_subprocess_exec.call_count == 1
    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "find"
    assert "-type" in args
    assert "d" in args
    assert "-name" in args
    assert "*tools*" in args

    assert result == "./src/utils\n./tests/tools"


@pytest.mark.asyncio
@patch("shutil.which", return_value="/usr/bin/rg")
@patch("asyncio.create_subprocess_exec")
async def test_search_content_with_rg(mock_subprocess_exec, mock_which):
    """Test content search using ripgrep (rg)."""
    mock_subprocess_exec.return_value = create_mock_process("main.py:10:def main():")

    result = await search_content("def main")

    mock_which.assert_called_once_with("rg")
    assert mock_subprocess_exec.call_count == 1
    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "rg"
    assert args[-1] == "."
    assert args[-2] == "def main"

    assert result == "main.py:10:def main():"


@pytest.mark.asyncio
@patch("shutil.which", return_value=None)
@patch("asyncio.create_subprocess_exec")
async def test_search_content_with_grep_fallback(mock_subprocess_exec, mock_which):
    """Test content search falling back to grep."""
    mock_subprocess_exec.return_value = create_mock_process("main.py:10:def main():")

    result = await search_content("def main")

    mock_which.assert_called_once_with("rg")
    assert mock_subprocess_exec.call_count == 1
    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "grep"
    assert "--exclude-dir=.git" in args  # Check for intelligent exclusions
    assert args[-1] == "."
    assert args[-2] == "def main"

    assert result == "main.py:10:def main():"


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_search_no_results(mock_subprocess_exec):
    """Test that a 'No results found.' message is returned for empty output."""
    mock_subprocess_exec.return_value = create_mock_process("")

    result = await search_files("*.nonexistent")

    assert result == "No results found."


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_search_command_error(mock_subprocess_exec):
    """Test that stderr from the command is returned as an error."""
    mock_subprocess_exec.return_value = create_mock_process(
        "", "find: unknown predicate `-badarg'", 1
    )

    result = await search_files("*")

    assert "Error executing search command:" in result
    assert "find: unknown predicate `-badarg'" in result
