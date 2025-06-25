"""Shared fixtures for tool tests."""

import pytest
from pydantic_ai import RunContext


@pytest.fixture
def mock_ctx():
    """Create a mock RunContext for testing."""
    return RunContext(
        deps=None,
        model=None,
        usage=None,
        prompt=None,
        messages=[],
        tool_call_id=None,
        tool_name=None,
        retry=0,
        run_step=0,
    )
