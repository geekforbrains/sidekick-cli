"""Shared fixtures and helpers for tests."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from pydantic_ai import messages

# ---------------------------------------------------------------------------
# Generic mocks
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_ui():
    """Return a mocked *ui* module/object."""
    return MagicMock()


@pytest.fixture
def mock_session():
    """Return a mocked *session* object."""
    return MagicMock()


@pytest.fixture
def mock_models():
    """Return a simple models mapping for tests that need it."""
    return {"model1": {}, "model2": {}, "model3": {}}


@pytest.fixture
def mock_config():
    """Return a minimal config dict."""
    return {
        "default_model": "claude-3-5-sonnet",
        "env": {},
        "settings": {},
    }


@pytest.fixture
def mock_usage():
    """Return a usage-like object with default numbers (can be tweaked inside tests)."""
    usage = MagicMock()
    usage.requests = 1
    usage.request_tokens = 1000
    usage.response_tokens = 500
    usage.total_tokens = 1500
    usage.details = []
    return usage


# ---------------------------------------------------------------------------
# Helper / factory fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_mock_process():
    """Factory to create an *asyncio* subprocess mock with the given stdout/stderr/returncode."""

    def _factory(stdout: str = "", stderr: str = "", returncode: int = 0):
        proc = AsyncMock()
        proc.communicate = AsyncMock(return_value=(stdout.encode(), stderr.encode()))
        proc.returncode = returncode
        return proc

    return _factory


@pytest.fixture
def make_tool_call():
    """Factory that produces a *messages.ToolCallPart*-like mock used in agent tests."""

    def _factory(name: str = "test_tool", call_id: str = "call_id"):
        tc = Mock(spec=messages.ToolCallPart)
        tc.part_kind = "tool-call"
        tc.tool_name = name
        tc.tool_call_id = call_id
        return tc

    return _factory


# ---------------------------------------------------------------------------
# Composite fixtures for common patching scenarios
# ---------------------------------------------------------------------------


@pytest.fixture
def patched_commands_env(monkeypatch, mock_ui, mock_session):
    """Patch *sidekick.commands.ui* and *.session* once for a whole test function."""
    import sidekick.commands as _cmd

    monkeypatch.setattr(_cmd, "ui", mock_ui)
    monkeypatch.setattr(_cmd, "session", mock_session)
    yield
