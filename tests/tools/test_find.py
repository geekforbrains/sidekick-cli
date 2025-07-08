"""Tests for the consolidated find tool."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai import RunContext

from sidekick.deps import ToolDeps
from sidekick.tools.find import find


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
async def test_find_files_with_fd(
    mock_subprocess_exec, mock_which, make_mock_process, mock_context
):
    mock_which.side_effect = lambda cmd: "/usr/bin/fd" if cmd == "fd" else None
    mock_subprocess_exec.return_value = make_mock_process("./src/main.py\n./src/agent.py")

    result = await find(mock_context, ".", "*.py")

    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "fd"
    assert "--type" in args and "f" in args
    assert "*.py" in args
    assert result == "./src/main.py\n./src/agent.py"


@pytest.mark.asyncio
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_find_dirs_with_fd(mock_subprocess_exec, mock_which, make_mock_process, mock_context):
    mock_which.side_effect = lambda cmd: "/usr/bin/fd" if cmd == "fd" else None
    mock_subprocess_exec.return_value = make_mock_process("./src/utils\n./tests/tools")

    result = await find(mock_context, ".", "*tools*", dirs=True)

    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "fd"
    assert "--type" in args and "d" in args
    assert "*tools*" in args
    assert result == "./src/utils\n./tests/tools"


@pytest.mark.asyncio
@patch("shutil.which", return_value="/usr/bin/rg")
@patch("asyncio.create_subprocess_exec")
async def test_find_content_with_rg(
    mock_subprocess_exec, mock_which, make_mock_process, mock_context
):
    mock_subprocess_exec.return_value = make_mock_process("main.py:10:def main():")

    result = await find(mock_context, ".", content="def main")

    mock_which.assert_called_once_with("rg")
    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "rg"
    assert "--line-number" in args
    assert args[-1] == "def main"
    assert result == "main.py:10:def main():"


@pytest.mark.asyncio
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_find_content_case_insensitive(
    mock_subprocess_exec, mock_which, make_mock_process, mock_context
):
    mock_which.return_value = "/usr/bin/rg"
    mock_subprocess_exec.return_value = make_mock_process("main.py:10:def MAIN():")

    result = await find(mock_context, ".", content="main", case_sensitive=False)

    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "rg"
    assert "-i" in args
    assert result == "main.py:10:def MAIN():"


@pytest.mark.asyncio
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_find_content_with_include_pattern(
    mock_subprocess_exec, mock_which, make_mock_process, mock_context
):
    mock_which.return_value = "/usr/bin/rg"
    mock_subprocess_exec.return_value = make_mock_process("test.py:5:import pytest")

    result = await find(mock_context, ".", content="import", include_pattern="*.py")

    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "rg"
    assert "--glob" in args
    glob_idx = args.index("--glob")
    assert args[glob_idx + 1] == "*.py"
    assert result == "test.py:5:import pytest"


@pytest.mark.asyncio
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_find_content_with_ag_fallback(
    mock_subprocess_exec, mock_which, make_mock_process, mock_context
):
    mock_which.side_effect = lambda cmd: "/usr/bin/ag" if cmd == "ag" else None
    mock_subprocess_exec.return_value = make_mock_process("main.py:10:def main():")

    result = await find(mock_context, ".", content="def main")

    args = mock_subprocess_exec.call_args[0]
    assert args[0] == "ag"
    assert "--line-numbers" in args
    assert args[-1] == "def main"
    assert result == "main.py:10:def main():"


@pytest.mark.asyncio
@patch("shutil.which")
@patch("os.walk")
@patch("builtins.open")
async def test_find_content_python_fallback(mock_open, mock_walk, mock_which, mock_context):
    mock_which.return_value = None
    mock_walk.return_value = [
        (".", ["src"], ["README.md"]),
        ("./src", [], ["main.py"]),
    ]

    mock_file = MagicMock()
    mock_file.__enter__.return_value = ["def main():\n", "    print('hello')\n"]
    mock_open.return_value = mock_file

    result = await find(mock_context, ".", content="def main")

    assert "main.py:1:def main():" in result


@pytest.mark.asyncio
@patch("shutil.which")
@patch("asyncio.create_subprocess_exec")
async def test_find_no_results(mock_subprocess_exec, mock_which, make_mock_process, mock_context):
    mock_which.side_effect = lambda cmd: "/usr/bin/fd" if cmd == "fd" else None
    mock_subprocess_exec.return_value = make_mock_process("")

    result = await find(mock_context, ".", "*.nonexistent")

    assert result == "No results found."


@pytest.mark.asyncio
@patch("shutil.which")
@patch("os.walk")
async def test_find_files_python_fallback(mock_walk, mock_which, mock_context):
    mock_which.return_value = None
    mock_walk.return_value = [
        (".", ["src"], ["README.md"]),
        ("./src", [], ["main.py", "utils.py"]),
    ]

    result = await find(mock_context, ".", "*.py")

    assert "./src/main.py" in result
    assert "./src/utils.py" in result
    assert "README.md" not in result
