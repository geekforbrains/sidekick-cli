"""
Tests for sidekick.tools.update_file module.
"""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from pydantic_ai.exceptions import ModelRetry

from sidekick.tools.update_file import update_file


@pytest.mark.asyncio
async def test_update_file_success():
    """Test successful file update operation."""
    original_content = "Hello, World!\nThis is a test file."
    target = "World"
    patch_text = "Universe"

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write(original_content)
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.update_file.info", new_callable=AsyncMock):
            result = await update_file(tmp_path, target, patch_text)
            assert result == f"File '{tmp_path}' updated successfully."

            with open(tmp_path, "r", encoding="utf-8") as f:
                updated_content = f.read()
                assert updated_content == "Hello, Universe!\nThis is a test file."
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_update_file_not_found_raises_model_retry():
    """Test that updating a non-existent file raises ModelRetry exception."""
    non_existent = "/path/that/does/not/exist.txt"

    with patch("sidekick.tools.update_file.info", new_callable=AsyncMock):
        with pytest.raises(ModelRetry) as exc_info:
            await update_file(non_existent, "target", "patch")

        assert "not found" in str(exc_info.value)
        assert "write_file" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_file_target_not_found_raises_model_retry():
    """Test that updating with non-existent target raises ModelRetry exception."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write("Hello, World!")
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.update_file.info", new_callable=AsyncMock):
            with pytest.raises(ModelRetry) as exc_info:
                await update_file(tmp_path, "Universe", "Galaxy")

            assert "Target block not found" in str(exc_info.value)
            assert "File starts with:" in str(exc_info.value)
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_update_file_no_changes_raises_model_retry():
    """Test that update with identical target and patch raises ModelRetry exception."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write("Hello, World!")
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.update_file.info", new_callable=AsyncMock):
            with pytest.raises(ModelRetry) as exc_info:
                await update_file(tmp_path, "World", "World")

            assert "no changes" in str(exc_info.value)
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_update_file_multiline_content():
    """Test updating multiline content."""
    original_content = """def hello():
    print("Hello, World!")
    return True"""

    target = 'print("Hello, World!")'
    patch_text = 'print("Hello, Universe!")'

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write(original_content)
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.update_file.info", new_callable=AsyncMock):
            result = await update_file(tmp_path, target, patch_text)
            assert result == f"File '{tmp_path}' updated successfully."

            with open(tmp_path, "r", encoding="utf-8") as f:
                updated_content = f.read()
                assert 'print("Hello, Universe!")' in updated_content
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_update_file_special_characters():
    """Test updating content with special characters."""
    original_content = "Special chars: é, ñ, 中文, 🚀"
    target = "中文"
    patch_text = "日本語"

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write(original_content)
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.update_file.info", new_callable=AsyncMock):
            result = await update_file(tmp_path, target, patch_text)
            assert result == f"File '{tmp_path}' updated successfully."

            with open(tmp_path, "r", encoding="utf-8") as f:
                updated_content = f.read()
                assert updated_content == "Special chars: é, ñ, 日本語, 🚀"
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_update_file_generic_exception():
    """Test handling of unexpected exceptions during file update."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write("content")
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.update_file.open", side_effect=PermissionError("Access denied")):
            with patch("sidekick.tools.update_file.error", new_callable=AsyncMock):
                result = await update_file(tmp_path, "content", "new")
                assert "Error updating file" in result
                assert "Access denied" in result
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_update_file_long_content_truncation_in_logs():
    """Test that long target/patch content is truncated in log messages."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write("x" * 100)
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.update_file.info", new_callable=AsyncMock) as mock_info:
            await update_file(tmp_path, "x" * 100, "y" * 100)

            log_call = mock_info.call_args[0][0]
            assert "..." in log_call
    finally:
        os.unlink(tmp_path)
