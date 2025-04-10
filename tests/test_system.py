import io
import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from sidekick.utils import system as system_module  # Rename to avoid conflict with pytest `system`
from sidekick.utils.system import get_sidekick_home, get_session_dir

# Mock Path.mkdir globally for tests in this module unless overridden
@pytest.fixture(autouse=True)
def mock_path_mkdir():
    with patch("sidekick.utils.system.Path.mkdir") as mock_mkdir:
        yield mock_mkdir


# === Tests for get_sidekick_home ===

@patch("sidekick.utils.system.Path.home")
def test_get_sidekick_home_creates_dir(mock_home, mock_path_mkdir):
    """Test that get_sidekick_home constructs the correct path and calls mkdir."""
    # Arrange
    fake_home_path = Path("/fake/home")
    expected_sidekick_path = fake_home_path / ".sidekick"
    mock_home.return_value = fake_home_path

    # Act
    result_path = get_sidekick_home()

    # Assert
    mock_home.assert_called_once()
    assert result_path == expected_sidekick_path
    # Check that mkdir was called correctly on the expected path instance
    # mock_path_mkdir is auto-used by the fixture
    mock_path_mkdir.assert_called_once_with(exist_ok=True)


@patch("sidekick.utils.system.Path.home")
def test_get_sidekick_home_returns_path(mock_home, mock_path_mkdir):
    """Test that the function returns the correct Path object."""
    # Arrange
    fake_home_path = Path("/another/fake/home")
    expected_sidekick_path = fake_home_path / ".sidekick"
    mock_home.return_value = fake_home_path

    # Act
    result_path = get_sidekick_home()

    # Assert
    assert isinstance(result_path, Path)
    assert result_path == expected_sidekick_path


# === Tests for _load_gitignore_patterns ===

# Since _load_gitignore_patterns is private, we access it via the module
_load_gitignore_patterns = system_module._load_gitignore_patterns

# We'll also need to patch DEFAULT_IGNORE_PATTERNS for consistent tests
@pytest.fixture(autouse=True)
def mock_default_ignore_patterns():
    """Replace DEFAULT_IGNORE_PATTERNS with a minimal set for testing."""
    original = system_module.DEFAULT_IGNORE_PATTERNS
    system_module.DEFAULT_IGNORE_PATTERNS = {"default_pattern/"} 
    yield
    system_module.DEFAULT_IGNORE_PATTERNS = original

# Creating test cases with mocked file contents
@patch("builtins.open")
@patch("io.open")  # Also patch io.open which is used in the function
def test_load_gitignore_patterns_reads_file(mock_io_open, mock_builtins_open):
    """Test reading patterns from a .gitignore file."""
    # Setup the file content mock
    file_content = """
# This is a comment
node_modules/
*.log
build/
/config.ini
    """
    
    # Configure the io.open mock (used in the function)
    mock_file = mock_open(read_data=file_content)
    mock_io_open.return_value = mock_file()
    
    # For demonstration, also mock builtins.open in case it's used
    mock_builtins_open.return_value = mock_file()
    
    # Call function with explicit path to avoid any .gitignore fallbacks
    patterns = system_module._load_gitignore_patterns("test.gitignore")
    
    # Check that we got a valid result
    assert patterns is not None
    
    # Check specific patterns
    assert "node_modules/" in patterns
    assert "*.log" in patterns
    assert "build/" in patterns
    assert "/config.ini" in patterns
    assert ".git/" in patterns  # .git/ is always added explicitly


@patch("builtins.open")
@patch("io.open")
def test_load_gitignore_patterns_empty_file(mock_io_open, mock_builtins_open):
    """Test reading an empty .gitignore file."""
    # Setup the empty file mock
    mock_file = mock_open(read_data="")
    mock_io_open.return_value = mock_file()
    mock_builtins_open.return_value = mock_file()
    
    # Call function with explicit path to avoid default patterns
    patterns = system_module._load_gitignore_patterns("test.gitignore")
    
    # Check result
    assert patterns is not None
    assert ".git/" in patterns  # Always added explicitly
    # Only the .git/ pattern should be present
    assert len(patterns) == 1


@patch("io.open", side_effect=FileNotFoundError())
def test_load_gitignore_patterns_file_not_found(mock_io_open):
    """Test handling when .gitignore file is not found."""
    # Call function with explicit path
    patterns = system_module._load_gitignore_patterns("nonexistent/.gitignore")
    
    # Function should return None when file is not found
    assert patterns is None


@patch("io.open", side_effect=IOError("Permission denied"))
@patch("builtins.print")  # Mock print to suppress error message during test
def test_load_gitignore_patterns_read_error(mock_print, mock_io_open):
    """Test handling other IOErrors during file read."""
    # Call function with explicit path
    patterns = system_module._load_gitignore_patterns("error.gitignore")
    
    # Function should return None on IOError
    assert patterns is None
    
    # Error message should be printed
    mock_print.assert_called_once()


@patch("builtins.open") 
@patch("io.open")
def test_load_gitignore_patterns_comments_and_empty_lines(mock_io_open, mock_builtins_open):
    """Test that comments and empty lines are ignored."""
    # Setup file with only comments and empty lines
    file_content = """
    # Only comments and empty lines
    
    # Another comment
    """
    mock_file = mock_open(read_data=file_content)
    mock_io_open.return_value = mock_file()
    mock_builtins_open.return_value = mock_file()
    
    # Call function with explicit path
    patterns = system_module._load_gitignore_patterns("comments.gitignore")
    
    # Should contain only .git/ for a file with no actual patterns
    assert patterns is not None
    assert ".git/" in patterns
    assert len(patterns) == 1


# === Tests for get_session_dir ===

@patch("sidekick.utils.system.get_sidekick_home") # Mock the dependency
@patch("sidekick.session.session_id", "test-session-123") # Mock session_id
def test_get_session_dir_constructs_path(mock_get_home, mock_path_mkdir):
    """Test get_session_dir constructs the path correctly and calls mkdir."""
    # Arrange
    fake_sidekick_home = Path("/fake/home/.sidekick")
    mock_get_home.return_value = fake_sidekick_home
    expected_session_path = fake_sidekick_home / "sessions" / "test-session-123"

    # Act
    result_path = get_session_dir()

    # Assert
    mock_get_home.assert_called_once()
    assert result_path == expected_session_path
    # Check mkdir call - mock_path_mkdir is from the autouse fixture
    mock_path_mkdir.assert_called_once_with(exist_ok=True, parents=True)


@patch("sidekick.utils.system.get_sidekick_home") # Mock the dependency
@patch("sidekick.session.session_id", "another-session-abc") # Mock session_id
def test_get_session_dir_returns_path(mock_get_home, mock_path_mkdir):
    """Test get_session_dir returns the correct Path object."""
    # Arrange
    fake_sidekick_home = Path("/fake/home/.sidekick")
    mock_get_home.return_value = fake_sidekick_home
    expected_session_path = fake_sidekick_home / "sessions" / "another-session-abc"

    # Act
    result_path = get_session_dir()

    # Assert
    assert isinstance(result_path, Path)
    assert result_path == expected_session_path
