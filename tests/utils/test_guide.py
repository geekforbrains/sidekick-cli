"""Tests for guide utility functions."""

import pytest

from sidekick.session import session
from sidekick.utils.guide import get_guide, load_guide


@pytest.fixture(autouse=True)
def _reset_session_project_guide():
    """Reset the cached guide before each test to avoid cross-test leakage."""
    original_value = session.project_guide
    session.project_guide = None
    yield
    session.project_guide = original_value


def test_load_guide_with_file(tmp_path, monkeypatch):
    """`load_guide` should return the file contents and cache them in the session."""

    guide_content = "# Project Guide\nUse Python 3.11"
    guide_path = tmp_path / "SIDEKICK.md"
    guide_path.write_text(guide_content)

    # Change current working directory to the temporary path containing the guide.
    monkeypatch.chdir(tmp_path)

    result = load_guide(session)
    assert result == guide_content
    assert session.project_guide == guide_content

    # Subsequent retrieval via `get_guide` should return the same cached value.
    assert get_guide(session) == guide_content


def test_load_guide_without_file(tmp_path, monkeypatch):
    """`load_guide` should return ``None`` when no guide file is present."""

    # Ensure the directory does **not** contain the guide file.
    monkeypatch.chdir(tmp_path)

    result = load_guide(session)
    assert result is None
    assert session.project_guide is None

    assert get_guide(session) is None
