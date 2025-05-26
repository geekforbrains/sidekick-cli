"""
Tests for sidekick.tools.write_file module.
"""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from pydantic_ai.exceptions import ModelRetry

from sidekick.tools.write_file import write_file


@pytest.mark.asyncio
async def test_write_file_success():
    """Test successful file write operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "new_file.txt")
        content = "Hello, World!"

        with patch("sidekick.tools.write_file.info", new_callable=AsyncMock):
            result = await write_file(filepath, content)
            assert result == f"Successfully wrote to new file: {filepath}"

            with open(filepath, "r", encoding="utf-8") as f:
                assert f.read() == content


@pytest.mark.asyncio
async def test_write_file_existing_file_raises_model_retry():
    """Test that writing to an existing file raises ModelRetry exception."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.write_file.info", new_callable=AsyncMock):
            with pytest.raises(ModelRetry) as exc_info:
                await write_file(tmp_path, "New content")

            assert "already exists" in str(exc_info.value)
            assert "update_file" in str(exc_info.value)
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_write_file_creates_parent_directories():
    """Test automatic parent directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "subdir", "nested", "file.txt")
        content = "Nested file content"

        with patch("sidekick.tools.write_file.info", new_callable=AsyncMock):
            result = await write_file(filepath, content)
            assert result == f"Successfully wrote to new file: {filepath}"
            assert os.path.exists(filepath)

            with open(filepath, "r", encoding="utf-8") as f:
                assert f.read() == content


@pytest.mark.asyncio
async def test_write_file_empty_content():
    """Test writing an empty file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "empty.txt")

        with patch("sidekick.tools.write_file.info", new_callable=AsyncMock):
            result = await write_file(filepath, "")
            assert result == f"Successfully wrote to new file: {filepath}"

            with open(filepath, "r", encoding="utf-8") as f:
                assert f.read() == ""


@pytest.mark.asyncio
async def test_write_file_special_characters():
    """Test writing files with special characters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "special.txt")
        content = "Special chars: é, ñ, 中文, 🚀\nMultiple\nLines"

        with patch("sidekick.tools.write_file.info", new_callable=AsyncMock):
            result = await write_file(filepath, content)
            assert result == f"Successfully wrote to new file: {filepath}"

            with open(filepath, "r", encoding="utf-8") as f:
                assert f.read() == content


@pytest.mark.asyncio
async def test_write_file_generic_exception():
    """Test handling of unexpected exceptions during file write."""
    filepath = "/invalid/path/file.txt"

    with patch("sidekick.tools.write_file.info", new_callable=AsyncMock):
        with patch("sidekick.tools.write_file.error", new_callable=AsyncMock):
            result = await write_file(filepath, "content")
            assert "Error writing file" in result


@pytest.mark.asyncio
async def test_write_file_long_content_truncation_in_logs():
    """Test that long content is truncated in log messages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "long.txt")
        content = "x" * 100

        with patch("sidekick.tools.write_file.info", new_callable=AsyncMock) as mock_info:
            await write_file(filepath, content)

            log_call = mock_info.call_args[0][0]
            assert "..." in log_call
            assert "content='" in log_call
            assert content not in log_call
