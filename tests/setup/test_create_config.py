import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.sidekick.constants import DEFAULT_USER_CONFIG
from src.sidekick.setup import create_config


def test_create_config_includes_all_defaults():
    """Test that create_config includes all default fields."""
    # Mock user inputs
    with patch("src.sidekick.setup.collect_api_keys") as mock_collect:
        with patch("src.sidekick.setup.select_default_model") as mock_select:
            mock_collect.return_value = {"OPENAI_API_KEY": "sk-test123"}
            mock_select.return_value = "gpt-4o"

            # Create temporary config file
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / ".config" / "sidekick.json"

                # Mock console to suppress output
                with patch("src.sidekick.setup.console"):
                    result = create_config(config_path)

                # Verify the returned config has all fields
                assert "default_model" in result
                assert result["default_model"] == "gpt-4o"

                assert "env" in result
                assert result["env"]["OPENAI_API_KEY"] == "sk-test123"
                # Should also have default placeholder values
                assert "ANTHROPIC_API_KEY" in result["env"]
                assert "GEMINI_API_KEY" in result["env"]

                assert "mcpServers" in result
                assert result["mcpServers"] == {}

                assert "settings" in result
                assert "allowed_tools" in result["settings"]
                assert result["settings"]["allowed_tools"] == ["read_file"]
                assert "allowed_commands" in result["settings"]
                assert len(result["settings"]["allowed_commands"]) > 0

                # Verify the file was written correctly
                with open(config_path) as f:
                    file_content = json.load(f)

                assert file_content == result


def test_create_config_with_no_api_keys():
    """Test create_config when user provides no API keys but continues anyway."""
    with patch("src.sidekick.setup.collect_api_keys") as mock_collect:
        with patch("src.sidekick.setup.select_default_model") as mock_select:
            with patch("src.sidekick.setup.Confirm.ask") as mock_confirm:
                mock_collect.return_value = {}
                mock_select.return_value = DEFAULT_USER_CONFIG["default_model"]
                mock_confirm.return_value = True  # Continue anyway

                with tempfile.TemporaryDirectory() as temp_dir:
                    config_path = Path(temp_dir) / ".config" / "sidekick.json"

                    with patch("src.sidekick.setup.console"):
                        result = create_config(config_path)

                    # Should have empty env dict, not the placeholder values
                    assert result["env"] == {}

                    # But should still have all other defaults
                    assert "settings" in result
                    assert "mcpServers" in result


def test_create_config_filters_empty_api_keys():
    """Test that empty string API keys are not included in the config."""
    # Mock user inputs - simulate user pressing enter without entering values
    with patch("src.sidekick.setup.Prompt.ask") as mock_prompt:
        with patch("src.sidekick.setup.select_default_model") as mock_select:
            # Simulate user pressing enter (empty string) for all API keys
            mock_prompt.side_effect = ["", "", ""]  # Empty strings for all 3 API keys
            mock_select.return_value = DEFAULT_USER_CONFIG["default_model"]

            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / ".config" / "sidekick.json"

                with patch("src.sidekick.setup.console"):
                    with patch("src.sidekick.setup.Confirm.ask", return_value=True):
                        result = create_config(config_path)

                # Should have empty env dict when all API keys are empty strings
                assert result["env"] == {}

                # But should still have all other defaults
                assert "default_model" in result
                assert "settings" in result
                assert "mcpServers" in result
