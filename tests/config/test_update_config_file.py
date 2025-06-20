"""Test update_config_file function."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from sidekick.config import ConfigError, update_config_file


def test_update_config_file_success():
    """Test successful config update."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {"default_model": "old-model", "env": {"KEY": "value"}}
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("sidekick.config.get_config_path", return_value=temp_path):
            update_config_file({"default_model": "new-model"})

            # Read back the updated config
            with open(temp_path) as f:
                updated = json.load(f)

            assert updated["default_model"] == "new-model"
            assert updated["env"]["KEY"] == "value"  # Other fields preserved
    finally:
        temp_path.unlink()


def test_update_config_file_no_config():
    """Test update when config doesn't exist."""
    with patch("sidekick.config.get_config_path", return_value=Path("/nonexistent/path")):
        with pytest.raises(ConfigError, match="Config file not found"):
            update_config_file({"default_model": "new-model"})


def test_update_config_file_merge_nested():
    """Test that nested dicts are merged, not replaced."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        config = {"env": {"KEY1": "value1", "KEY2": "value2"}}
        json.dump(config, f)
        temp_path = Path(f.name)

    try:
        with patch("sidekick.config.get_config_path", return_value=temp_path):
            update_config_file({"env": {"KEY2": "updated", "KEY3": "new"}})

            with open(temp_path) as f:
                updated = json.load(f)

            assert updated["env"]["KEY1"] == "value1"  # Preserved
            assert updated["env"]["KEY2"] == "updated"  # Updated
            assert updated["env"]["KEY3"] == "new"  # Added
    finally:
        temp_path.unlink()
