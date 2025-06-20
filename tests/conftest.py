"""Common test fixtures and utilities for sidekick tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_ui():
    """Mock UI object for testing."""
    return MagicMock()


@pytest.fixture
def mock_session():
    """Mock session object for testing."""
    return MagicMock()


@pytest.fixture
def mock_models():
    """Mock models dictionary for testing."""
    return {"model1": {}, "model2": {}, "model3": {}}


@pytest.fixture
def mock_config():
    """Mock config dictionary for testing."""
    return {
        "default_model": "claude-3-5-sonnet",
        "env": {},
        "settings": {},
    }


@pytest.fixture
def mock_usage():
    """Mock usage object for testing."""
    usage = MagicMock()
    usage.requests = 1
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.total_tokens = 1500
    usage.details = []
    return usage
