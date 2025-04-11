import json
from unittest.mock import mock_open, patch

from sidekick import config, session
from sidekick.utils import user_config


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps({"default_model": "test_model", "env": {}}),
)
@patch("json.load", return_value={"default_model": "test_model", "env": {}})
def test_load_config_success(mock_json_load, mock_file):
    """Test loading a valid config file"""
    result = user_config.load_config()
    mock_file.assert_called_once_with(config.CONFIG_FILE, "r")
    mock_json_load.assert_called_once_with(mock_file())
    assert result == {"default_model": "test_model", "env": {}}


@patch("builtins.open", side_effect=FileNotFoundError)
def test_load_config_not_found(mock_file):
    """Test loading when config file does not exist"""
    result = user_config.load_config()
    mock_file.assert_called_once_with(config.CONFIG_FILE, "r")
    assert result is None


@patch("builtins.open", new_callable=mock_open, read_data="invalid json")
@patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0))
def test_load_config_invalid_json(mock_json_load, mock_file):
    """Test loading an invalid config file"""
    result = user_config.load_config()
    mock_file.assert_called_once_with(config.CONFIG_FILE, "r")
    mock_json_load.assert_called_once_with(mock_file())
    assert result is None


@patch("json.dump")
@patch("builtins.open", new_callable=mock_open)
def test_save_config_success(mock_file, mock_json_dump):
    """Test saving the config successfully"""
    session.user_config = {"default_model": "save_test", "env": {"KEY": "VALUE"}}
    result = user_config.save_config()
    mock_file.assert_called_once_with(config.CONFIG_FILE, "w")
    mock_json_dump.assert_called_once_with(session.user_config, mock_file(), indent=4)
    assert result is True


@patch("builtins.open", side_effect=IOError)
def test_save_config_failure(mock_file):
    """Test saving the config when an IO error occurs"""
    session.user_config = {"default_model": "save_fail"}
    result = user_config.save_config()
    mock_file.assert_called_once_with(config.CONFIG_FILE, "w")
    assert result is False


@patch("sidekick.utils.user_config.save_config", return_value=True)
def test_set_default_model_success(mock_save_config):
    """Test setting the default model successfully"""
    session.user_config = {"default_model": "old_model"}
    new_model = "new_default_model"
    result = user_config.set_default_model(new_model)

    assert session.user_config["default_model"] == new_model
    mock_save_config.assert_called_once()
    assert result is True


@patch("sidekick.utils.user_config.save_config", return_value=False)
def test_set_default_model_save_fails(mock_save_config):
    """Test setting the default model when saving fails"""
    session.user_config = {"default_model": "old_model_fail"}
    new_model = "new_default_model_fail"
    result = user_config.set_default_model(new_model)

    assert session.user_config["default_model"] == new_model
    mock_save_config.assert_called_once()
    assert result is False
