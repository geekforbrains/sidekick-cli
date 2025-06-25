"""Tests for the search tool – refactored to use shared fixtures and parametrize."""

from unittest.mock import patch

import pytest

from sidekick.tools.search import search_content, search_dirs, search_files


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_search_files_success(mock_subprocess_exec, make_mock_process):
    mock_subprocess_exec.return_value = make_mock_process("./src/main.py\n./src/agent.py")

    result = await search_files("*.py")

    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "find" and "-type" in args and "f" in args and "*.py" in args
    assert result == "./src/main.py\n./src/agent.py"


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_search_dirs_success(mock_subprocess_exec, make_mock_process):
    mock_subprocess_exec.return_value = make_mock_process("./src/utils\n./tests/tools")

    result = await search_dirs("*tools*")

    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "find" and "-type" in args and "d" in args and "*tools*" in args
    assert result == "./src/utils\n./tests/tools"


@pytest.mark.asyncio
@patch("shutil.which", return_value="/usr/bin/rg")
@patch("asyncio.create_subprocess_exec")
async def test_search_content_with_rg(mock_subprocess_exec, mock_which, make_mock_process):
    mock_subprocess_exec.return_value = make_mock_process("main.py:10:def main():")

    result = await search_content("def main")

    mock_which.assert_called_once_with("rg")
    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "rg" and args[-2] == "def main" and args[-1] == "."
    assert result == "main.py:10:def main():"


@pytest.mark.asyncio
@patch("shutil.which", return_value=None)
@patch("asyncio.create_subprocess_exec")
async def test_search_content_with_grep_fallback(
    mock_subprocess_exec, mock_which, make_mock_process
):
    mock_subprocess_exec.return_value = make_mock_process("main.py:10:def main():")

    result = await search_content("def main")

    mock_which.assert_called_once_with("rg")
    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "grep" and "--exclude-dir=.git" in args and args[-2] == "def main"
    assert result == "main.py:10:def main():"


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_search_no_results(mock_subprocess_exec, make_mock_process):
    mock_subprocess_exec.return_value = make_mock_process("")
    assert await search_files("*.nonexistent") == "No results found."


@pytest.mark.asyncio
@patch("asyncio.create_subprocess_exec")
async def test_search_command_error(mock_subprocess_exec, make_mock_process):
    mock_subprocess_exec.return_value = make_mock_process(
        "", "find: unknown predicate `-badarg'", 1
    )

    result = await search_files("*")
    assert "Error executing search command:" in result and "badarg" in result
