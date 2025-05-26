"""
Tests for sidekick.tools.run_command module.
"""

import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sidekick.constants import (CMD_OUTPUT_FORMAT, CMD_OUTPUT_NO_ERRORS, CMD_OUTPUT_NO_OUTPUT,
                                CMD_OUTPUT_TRUNCATED, ERROR_COMMAND_EXECUTION,
                                MAX_COMMAND_OUTPUT)
from sidekick.tools.run_command import run_command


@pytest.mark.asyncio
async def test_run_command_success():
    """Test successful command execution with output."""
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("Hello, World!", "")
    
    with patch("subprocess.Popen", return_value=mock_process):
        with patch("sidekick.tools.run_command.info", new_callable=AsyncMock):
            result = await run_command("echo 'Hello, World!'")
            expected = CMD_OUTPUT_FORMAT.format(
                output="Hello, World!",
                error=CMD_OUTPUT_NO_ERRORS
            ).strip()
            assert result == expected


@pytest.mark.asyncio
async def test_run_command_no_output():
    """Test command with no output."""
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("", "")
    
    with patch("subprocess.Popen", return_value=mock_process):
        with patch("sidekick.tools.run_command.info", new_callable=AsyncMock):
            result = await run_command("true")
            expected = CMD_OUTPUT_FORMAT.format(
                output=CMD_OUTPUT_NO_OUTPUT,
                error=CMD_OUTPUT_NO_ERRORS
            ).strip()
            assert result == expected


@pytest.mark.asyncio
async def test_run_command_with_stderr():
    """Test command with stderr output."""
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("", "Error occurred")
    
    with patch("subprocess.Popen", return_value=mock_process):
        with patch("sidekick.tools.run_command.info", new_callable=AsyncMock):
            result = await run_command("command_with_error")
            expected = CMD_OUTPUT_FORMAT.format(
                output=CMD_OUTPUT_NO_OUTPUT,
                error="Error occurred"
            ).strip()
            assert result == expected


@pytest.mark.asyncio
async def test_run_command_output_truncation():
    """Test output truncation for large outputs."""
    large_output = "x" * (MAX_COMMAND_OUTPUT + 100)
    mock_process = MagicMock()
    mock_process.communicate.return_value = (large_output, "")
    
    with patch("subprocess.Popen", return_value=mock_process):
        with patch("sidekick.tools.run_command.info", new_callable=AsyncMock):
            result = await run_command("generate_large_output")
            
            assert CMD_OUTPUT_TRUNCATED in result
            assert len(result) < len(large_output)
            assert result.startswith("STDOUT:\n")


@pytest.mark.asyncio
async def test_run_command_file_not_found():
    """Test command execution with FileNotFoundError."""
    with patch("subprocess.Popen", side_effect=FileNotFoundError("command not found")):
        with patch("sidekick.tools.run_command.error", new_callable=AsyncMock) as mock_error:
            result = await run_command("nonexistent_command")
            
            expected = ERROR_COMMAND_EXECUTION.format(
                command="nonexistent_command",
                error="command not found"
            )
            assert result == expected
            mock_error.assert_called_once_with(expected)


@pytest.mark.asyncio
async def test_run_command_general_exception():
    """Test command execution with general exception."""
    with patch("subprocess.Popen", side_effect=Exception("Unexpected error")):
        with patch("sidekick.tools.run_command.error", new_callable=AsyncMock) as mock_error:
            result = await run_command("problematic_command")
            
            expected = "Error running command 'problematic_command': Unexpected error"
            assert result == expected
            mock_error.assert_called_once_with(expected)


@pytest.mark.asyncio
async def test_run_command_shell_parameters():
    """Test that subprocess.Popen is called with correct parameters."""
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("output", "")
    
    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        with patch("sidekick.tools.run_command.info", new_callable=AsyncMock):
            await run_command("test command")
            
            mock_popen.assert_called_once_with(
                "test command",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )


@pytest.mark.asyncio
async def test_run_command_mixed_output():
    """Test command with both stdout and stderr."""
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("Standard output", "Error output")
    
    with patch("subprocess.Popen", return_value=mock_process):
        with patch("sidekick.tools.run_command.info", new_callable=AsyncMock):
            result = await run_command("mixed_output_command")
            expected = CMD_OUTPUT_FORMAT.format(
                output="Standard output",
                error="Error output"
            ).strip()
            assert result == expected