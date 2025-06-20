"""Tests for validate_config_structure function."""

import pytest

from sidekick.config import ConfigValidationError, validate_config_structure


def test_valid_config_passes():
    """Test that valid config passes validation."""
    config = {"default_model": "test-model", "env": {"API_KEY": "test"}}
    # Should not raise
    validate_config_structure(config)


def test_valid_config_with_empty_env():
    """Test valid config with empty env dict."""
    config = {"default_model": "test-model", "env": {}}
    # Should not raise
    validate_config_structure(config)


def test_raises_for_non_dict():
    """Test ConfigValidationError for non-dict config."""
    with pytest.raises(ConfigValidationError) as exc_info:
        validate_config_structure("not a dict")
    assert "Config must be a JSON object" in str(exc_info.value)


def test_raises_for_missing_default_model():
    """Test ConfigValidationError when default_model missing."""
    with pytest.raises(ConfigValidationError) as exc_info:
        validate_config_structure({"env": {}})
    assert "Config missing required field 'default_model'" in str(exc_info.value)


def test_raises_for_non_string_default_model():
    """Test ConfigValidationError when default_model not string."""
    with pytest.raises(ConfigValidationError) as exc_info:
        validate_config_structure({"default_model": 123, "env": {}})
    assert "'default_model' must be a string" in str(exc_info.value)


def test_raises_for_missing_env():
    """Test ConfigValidationError when env field missing."""
    with pytest.raises(ConfigValidationError) as exc_info:
        validate_config_structure({"default_model": "test-model"})
    assert "Config missing required field 'env'" in str(exc_info.value)


def test_raises_for_non_dict_env():
    """Test ConfigValidationError when env is not a dict."""
    with pytest.raises(ConfigValidationError) as exc_info:
        validate_config_structure({"default_model": "test", "env": "not a dict"})
    assert "'env' field must be an object" in str(exc_info.value)
