"""
Tests for sidekick.tools.read_file module.
"""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

from sidekick.constants import (ERROR_FILE_DECODE, ERROR_FILE_NOT_FOUND, ERROR_FILE_TOO_LARGE,
                                MAX_FILE_SIZE)
from sidekick.tools.read_file import read_file


@pytest.mark.asyncio
async def test_read_file_success():
    """Test successful file read operation."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write("Hello, World!")
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.read_file.info", new_callable=AsyncMock):
            result = await read_file(tmp_path)
            assert result == "Hello, World!"
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_read_file_not_found():
    """Test reading a non-existent file."""
    non_existent = "/path/that/does/not/exist.txt"

    with patch("sidekick.tools.read_file.error", new_callable=AsyncMock):
        result = await read_file(non_existent)
        assert ERROR_FILE_NOT_FOUND.format(filepath=non_existent) in result


@pytest.mark.asyncio
async def test_read_file_size_limit():
    """Test file size limit enforcement."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write("x" * (MAX_FILE_SIZE + 1))
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.read_file.error", new_callable=AsyncMock):
            result = await read_file(tmp_path)
            assert ERROR_FILE_TOO_LARGE.format(filepath=tmp_path) in result
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_read_file_unicode_decode_error():
    """Test handling of files with invalid UTF-8 encoding."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp:
        tmp.write(b"\xff\xfe\x00\x00")
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.read_file.error", new_callable=AsyncMock):
            result = await read_file(tmp_path)
            assert ERROR_FILE_DECODE.format(filepath=tmp_path) in result
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_read_empty_file():
    """Test reading an empty file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.read_file.info", new_callable=AsyncMock):
            result = await read_file(tmp_path)
            assert result == ""
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_read_file_with_special_characters():
    """Test reading files with various special characters and encodings."""
    content = "Special chars: é, ñ, 中文, 🚀\nMultiple\nLines"

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.read_file.info", new_callable=AsyncMock):
            result = await read_file(tmp_path)
            assert result == content
    finally:
        os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_read_file_generic_exception():
    """Test handling of unexpected exceptions during file read."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
        tmp_path = tmp.name

    try:
        with patch("sidekick.tools.read_file.open", side_effect=PermissionError("Access denied")):
            with patch("sidekick.tools.read_file.error", new_callable=AsyncMock):
                result = await read_file(tmp_path)
                assert "Error reading file" in result
                assert "Access denied" in result
    finally:
        os.unlink(tmp_path)
