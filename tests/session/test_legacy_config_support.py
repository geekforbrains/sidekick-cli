from src.sidekick.session import Session


def test_supports_allowed_tools():
    """Test that new allowed_tools field is supported."""
    config = {
        "default_model": "claude-3-5-sonnet",
        "env": {},
        "settings": {
            "allowed_tools": ["read_file", "list_files"],
            "allowed_commands": ["grep", "pwd"],
        },
    }

    session = Session()
    session.init(config, "claude-3-5-sonnet")

    assert "read_file" in session.skip_confirmations
    assert "list_files" in session.skip_confirmations
    assert "grep" in session.allowed_commands
    assert "pwd" in session.allowed_commands


def test_supports_legacy_tool_ignore():
    """Test backward compatibility with tool_ignore."""
    config = {
        "default_model": "claude-3-5-sonnet",
        "env": {},
        "settings": {"tool_ignore": ["bash", "write_file"], "allowed_commands": ["ls", "cat"]},
    }

    session = Session()
    session.init(config, "claude-3-5-sonnet")

    assert "bash" in session.skip_confirmations
    assert "write_file" in session.skip_confirmations
    assert "ls" in session.allowed_commands
    assert "cat" in session.allowed_commands


def test_supports_both_fields():
    """Test that both allowed_tools and tool_ignore work together."""
    config = {
        "default_model": "claude-3-5-sonnet",
        "env": {},
        "settings": {
            "allowed_tools": ["read_file"],
            "tool_ignore": ["bash"],
            "allowed_commands": ["ls"],
        },
    }

    session = Session()
    session.init(config, "claude-3-5-sonnet")

    assert "read_file" in session.skip_confirmations
    assert "bash" in session.skip_confirmations
    assert "ls" in session.allowed_commands


def test_empty_settings():
    """Test initialization with empty settings."""
    config = {"default_model": "claude-3-5-sonnet", "env": {}, "settings": {}}

    session = Session()
    session.init(config, "claude-3-5-sonnet")

    assert len(session.skip_confirmations) == 0
    assert len(session.allowed_commands) == 0


def test_no_settings_key():
    """Test initialization without settings key."""
    config = {"default_model": "claude-3-5-sonnet", "env": {}}

    session = Session()
    session.init(config, "claude-3-5-sonnet")

    assert len(session.skip_confirmations) == 0
    assert len(session.allowed_commands) == 0
