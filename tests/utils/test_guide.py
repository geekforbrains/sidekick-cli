"""Tests for guide utility functions."""

from sidekick.utils.guide import load_guide


def test_load_guide_with_file(tmp_path, monkeypatch):
    """`load_guide` should return the file contents."""

    guide_content = "# Project Guide\nUse Python 3.11"
    guide_path = tmp_path / "SIDEKICK.md"
    guide_path.write_text(guide_content)

    monkeypatch.chdir(tmp_path)

    result = load_guide()
    assert result == guide_content


def test_load_guide_without_file(tmp_path, monkeypatch):
    """`load_guide` should return ``None`` when no guide file is present."""

    monkeypatch.chdir(tmp_path)

    result = load_guide()
    assert result is None
