import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from src.sidekick.config import ConfigError, ensure_config_structure
from src.sidekick.constants import DEFAULT_USER_CONFIG


def test_preserves_user_settings():
    """Test that existing user settings are preserved."""
    user_config = {
        "default_model": "gpt-4o",
        "env": {"OPENAI_API_KEY": "sk-user123", "CUSTOM_KEY": "custom-value"},
        "settings": {
            "allowed_tools": ["bash", "write_file"],
            "allowed_commands": ["rm", "mv", "cp"],
        },
        "mcpServers": {"myserver": {"command": "node", "args": ["server.js"]}},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(user_config, f, indent=2)
        temp_path = Path(f.name)

    try:
        with patch("src.sidekick.config.get_config_path", return_value=temp_path):
            result = ensure_config_structure()

            # User values should be preserved
            assert result["default_model"] == "gpt-4o"
            assert result["env"]["OPENAI_API_KEY"] == "sk-user123"
            assert result["env"]["CUSTOM_KEY"] == "custom-value"
            assert result["settings"]["allowed_tools"] == ["bash", "write_file"]
            assert result["settings"]["allowed_commands"] == ["rm", "mv", "cp"]
            assert "myserver" in result["mcpServers"]

            # Default values should still be present for missing keys
            assert "ANTHROPIC_API_KEY" in result["env"]
            assert "GEMINI_API_KEY" in result["env"]
    finally:
        temp_path.unlink()


def test_adds_missing_defaults():
    """Test that missing fields are added with defaults."""
    minimal_config = {
        "default_model": "claude-3-5-sonnet",
        "env": {"ANTHROPIC_API_KEY": "sk-ant123"},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(minimal_config, f, indent=2)
        temp_path = Path(f.name)

    try:
        with patch("src.sidekick.config.get_config_path", return_value=temp_path):
            result = ensure_config_structure()

            # User values preserved
            assert result["default_model"] == "claude-3-5-sonnet"
            assert result["env"]["ANTHROPIC_API_KEY"] == "sk-ant123"

            # Missing fields added
            assert "mcpServers" in result
            assert result["mcpServers"] == {}
            assert "settings" in result
            assert result["settings"]["allowed_tools"] == ["read_file"]
            assert len(result["settings"]["allowed_commands"]) > 0
            assert "ls" in result["settings"]["allowed_commands"]

            # Verify file was updated
            with open(temp_path) as f:
                file_content = json.load(f)
            assert "settings" in file_content
            assert "mcpServers" in file_content
    finally:
        temp_path.unlink()


def test_does_not_add_tool_ignore_field():
    """Test that tool_ignore is not added to config when updating."""
    config_with_legacy = {
        "default_model": "gpt-4o",
        "env": {"OPENAI_API_KEY": "sk-123"},
        "settings": {"tool_ignore": ["bash", "write_file"]},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_with_legacy, f, indent=2)
        temp_path = Path(f.name)

    try:
        with patch("src.sidekick.config.get_config_path", return_value=temp_path):
            result = ensure_config_structure()

            # Should have allowed_tools from defaults
            assert "allowed_tools" in result["settings"]

            # Should still have tool_ignore (preserved, not removed)
            assert "tool_ignore" in result["settings"]
            assert result["settings"]["tool_ignore"] == ["bash", "write_file"]

            # Verify the file still has tool_ignore
            with open(temp_path) as f:
                file_content = json.load(f)
            assert file_content["settings"]["tool_ignore"] == ["bash", "write_file"]
    finally:
        temp_path.unlink()


def test_empty_config_gets_full_defaults():
    """Test that an empty config gets all defaults."""
    empty_config = {}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(empty_config, f, indent=2)
        temp_path = Path(f.name)

    try:
        with patch("src.sidekick.config.get_config_path", return_value=temp_path):
            # This should fail validation before ensure_config_structure is called
            # but let's test the merge behavior anyway
            with patch("src.sidekick.config.validate_config_structure"):
                result = ensure_config_structure()

                # Should have all defaults
                assert result == DEFAULT_USER_CONFIG
    finally:
        temp_path.unlink()


def test_no_file_update_when_no_changes():
    """Test that file is not rewritten when no changes are needed."""
    # Config that already has all expected fields
    complete_config = {
        "default_model": "claude-3-5-sonnet-20241022",
        "env": {
            "ANTHROPIC_API_KEY": "your-anthropic-api-key",
            "OPENAI_API_KEY": "your-openai-api-key",
            "GEMINI_API_KEY": "your-gemini-api-key",
        },
        "mcpServers": {},
        "settings": {
            "allowed_tools": ["read_file"],
            "allowed_commands": [
                "ls",
                "cat",
                "grep",
                "rg",
                "find",
                "pwd",
                "echo",
                "which",
                "head",
                "tail",
                "wc",
                "sort",
                "uniq",
                "diff",
                "tree",
                "file",
                "stat",
                "du",
                "df",
                "ps",
                "top",
                "env",
                "date",
                "whoami",
                "hostname",
                "uname",
                "id",
                "groups",
                "history",
            ],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(complete_config, f, indent=2)
        temp_path = Path(f.name)

    # Small delay to ensure different mtime if file is modified
    time.sleep(0.01)
    original_mtime = temp_path.stat().st_mtime

    try:
        with patch("src.sidekick.config.get_config_path", return_value=temp_path):
            result = ensure_config_structure()

            # Should return the same config
            assert result == complete_config

            # File should not have been modified
            assert temp_path.stat().st_mtime == original_mtime
    finally:
        temp_path.unlink()


def test_raises_config_error_on_missing_file():
    """Test that ConfigError is raised when config file doesn't exist."""
    non_existent_path = Path("/tmp/does_not_exist_12345.json")

    with patch("src.sidekick.config.get_config_path", return_value=non_existent_path):
        with pytest.raises(ConfigError):
            ensure_config_structure()
