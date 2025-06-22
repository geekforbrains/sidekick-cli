"""Tests for input utilities."""

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from sidekick.utils.input import (PLACEHOLDER_STYLE, PLACEHOLDER_TEXT, PROMPT_CONTINUATION_INDENT,
                                  PROMPT_SYMBOL, create_multiline_keybindings,
                                  create_multiline_prompt_session, create_prompt_style,
                                  prompt_continuation)


def test_create_multiline_keybindings():
    """Test that keybindings are created correctly."""
    bindings = create_multiline_keybindings()
    assert isinstance(bindings, KeyBindings)
    assert len(bindings.bindings) > 0


def test_create_prompt_style():
    """Test that prompt style is created correctly."""
    style = create_prompt_style()
    assert isinstance(style, Style)
    style_dict = dict(style.style_rules)
    assert "placeholder" in style_dict
    assert style_dict["placeholder"] == PLACEHOLDER_STYLE


def test_prompt_continuation():
    """Test prompt continuation returns correct indentation."""
    # Should always return the same indentation regardless of parameters
    assert prompt_continuation(80, 0, False) == PROMPT_CONTINUATION_INDENT
    assert prompt_continuation(120, 5, True) == PROMPT_CONTINUATION_INDENT
    assert prompt_continuation(60, 10, False) == PROMPT_CONTINUATION_INDENT


def test_create_multiline_prompt_session():
    """Test that prompt session is created with correct configuration."""
    session = create_multiline_prompt_session()
    assert isinstance(session, PromptSession)
    assert session.multiline is True
    assert session.prompt_continuation == prompt_continuation


def test_constants():
    """Test that constants have expected values."""
    assert PROMPT_SYMBOL == "> "
    assert PROMPT_CONTINUATION_INDENT == "  "
    assert PLACEHOLDER_TEXT == "Type something, esc+enter to submit"
