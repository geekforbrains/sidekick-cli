"""Tests for the new grep and find tools."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai import RunContext

from sidekick.deps import ToolDeps
from sidekick.tools.find import find
from sidekick.tools.grep import grep


@pytest.fixture
def mock_context():
    """Create a mock RunContext with ToolDeps."""
    mock_deps = MagicMock(spec=ToolDeps)
    mock_deps.display_tool_status = None
    mock_ctx = MagicMock(spec=RunContext)
    mock_ctx.deps = mock_deps
    return mock_ctx


@pytest.mark.asyncio
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_find_files_success(
    mock_subprocess_exec, mock_which, make_mock_process, mock_context
):
    # Make fd, rg unavailable so it falls back to find
    mock_which.side_effect = lambda cmd: "/usr/bin/find" if cmd == "find" else None
    mock_subprocess_exec.return_value = make_mock_process("./src/main.py\n./src/agent.py")

    result = await find(mock_context, ".", "*.py")

    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "find" and "-type" in args and "f" in args and "*.py" in args
    assert result == "./src/main.py\n./src/agent.py"


@pytest.mark.asyncio
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_find_dirs_success(mock_subprocess_exec, mock_which, make_mock_process, mock_context):
    # Make fd, rg unavailable so it falls back to find
    mock_which.side_effect = lambda cmd: "/usr/bin/find" if cmd == "find" else None
    mock_subprocess_exec.return_value = make_mock_process("./src/utils\n./tests/tools")

    result = await find(mock_context, ".", "*tools*", dirs=True)

    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "find" and "-type" in args and "d" in args and "*tools*" in args
    assert result == "./src/utils\n./tests/tools"


@pytest.mark.asyncio
@patch("shutil.which", return_value="/usr/bin/rg")
@patch("asyncio.create_subprocess_exec")
async def test_grep_with_rg(mock_subprocess_exec, mock_which, make_mock_process, mock_context):
    mock_subprocess_exec.return_value = make_mock_process("main.py:10:def main():")

    result = await grep(mock_context, ".", "def main")

    mock_which.assert_called_once_with("rg")
    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "rg" and args[-2] == "def main" and args[-1] == "."
    assert result == "main.py:10:def main():"


@pytest.mark.asyncio
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_grep_with_grep_fallback(
    mock_subprocess_exec, mock_which, make_mock_process, mock_context
):
    # Make rg and ag unavailable, but grep available
    mock_which.side_effect = lambda cmd: "/usr/bin/grep" if cmd == "grep" else None
    mock_subprocess_exec.return_value = make_mock_process("main.py:10:def main():")

    result = await grep(mock_context, ".", "def main")

    # Check that it tried rg, ag, then grep
    assert mock_which.call_count >= 3
    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "grep" and "--exclude-dir=.git" in args and args[-2] == "def main"
    assert result == "main.py:10:def main():"


@pytest.mark.asyncio
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_find_no_results(mock_subprocess_exec, mock_which, make_mock_process, mock_context):
    # Make fd, rg unavailable so it falls back to find
    mock_which.side_effect = lambda cmd: "/usr/bin/find" if cmd == "find" else None
    mock_subprocess_exec.return_value = make_mock_process("")
    assert await find(mock_context, ".", "*.nonexistent") == "No results found."


@pytest.mark.asyncio
@patch("shutil.which")
@patch("pathlib.Path.rglob")
async def test_find_command_error(mock_rglob, mock_which, mock_context):
    # Make all external tools unavailable to force Python fallback
    mock_which.return_value = None
    # Mock the Python fallback to return results
    mock_rglob.return_value = []

    result = await find(mock_context, ".", "*")
    assert result == "No results found."
