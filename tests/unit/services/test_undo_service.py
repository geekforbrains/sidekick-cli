"""
Tests for sidekick.services.undo_service module.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic_ai.messages import ModelResponse, TextPart

from sidekick.constants import UNDO_INITIAL_COMMIT
from sidekick.exceptions import GitOperationError
from sidekick.services import undo_service
from sidekick.types import SessionState


@pytest.fixture
def mock_session():
    """Create a mock SessionState for testing."""
    session = Mock(spec=SessionState)
    session.session_id = "test-session-123"
    session.messages = []
    return session


@pytest.fixture
def mock_session_dir(tmp_path):
    """Create a temporary session directory."""
    session_dir = tmp_path / ".sidekick" / "sessions" / "test-session-123"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


class TestSystemDirectoryChecks:
    """Test system directory detection and safety checks."""

    def test_is_system_directory_root(self):
        """Test detection of root directory."""
        assert undo_service.is_system_directory(Path("/"))

    def test_is_system_directory_usr(self):
        """Test detection of /usr directory."""
        assert undo_service.is_system_directory(Path("/usr"))
        assert undo_service.is_system_directory(Path("/usr/bin"))

    def test_is_system_directory_windows(self):
        """Test detection of Windows system directories."""
        assert undo_service.is_system_directory(Path("/Windows"))
        assert undo_service.is_system_directory(Path("/Program Files"))

    def test_is_system_directory_safe(self):
        """Test safe directories are not flagged as system."""
        assert not undo_service.is_system_directory(Path("/home/user/project"))
        assert not undo_service.is_system_directory(Path("/tmp/test"))

    def test_count_files_in_directory(self, tmp_path):
        """Test file counting in directory."""
        for i in range(10):
            (tmp_path / f"file{i}.txt").touch()
        
        assert undo_service.count_files_in_directory(tmp_path) == 10
        assert undo_service.count_files_in_directory(tmp_path, limit=5) == 5

    def test_count_files_permission_error(self):
        """Test file counting with permission errors."""
        with patch("pathlib.Path.iterdir", side_effect=PermissionError):
            result = undo_service.count_files_in_directory(Path("/test"))
            assert result == 0

    def test_is_safe_for_undo_system_directory(self):
        """Test safety check for system directories."""
        with patch.object(undo_service, "is_system_directory", return_value=True):
            is_safe, reason = undo_service.is_safe_for_undo(Path("/usr"))
            assert not is_safe
            assert reason == "System directory"

    def test_is_safe_for_undo_too_close_to_root(self):
        """Test safety check for directories too close to root."""
        is_safe, reason = undo_service.is_safe_for_undo(Path("/home"))
        assert not is_safe
        assert reason == "Too close to filesystem root"

    def test_is_safe_for_undo_too_many_files(self, tmp_path):
        """Test safety check for directories with too many files."""
        with patch.object(undo_service, "count_files_in_directory", return_value=5000):
            is_safe, reason = undo_service.is_safe_for_undo(tmp_path)
            assert not is_safe
            assert reason == "Directory contains too many files"

    def test_is_safe_for_undo_success(self, tmp_path):
        """Test successful safety check."""
        project_dir = tmp_path / "home" / "user" / "project"
        project_dir.mkdir(parents=True)
        is_safe, reason = undo_service.is_safe_for_undo(project_dir)
        assert is_safe
        assert reason == "Safe for undo operations"


class TestUndoStatus:
    """Test undo status checking functionality."""

    def test_get_undo_status_home_directory(self, mock_session):
        """Test undo status when running from home directory."""
        with patch("pathlib.Path.cwd", return_value=Path.home()):
            is_available, message = undo_service.get_undo_status(mock_session)
            assert not is_available
            assert message == "Disabled (running from home directory)"

    def test_get_undo_status_unsafe_directory(self, mock_session):
        """Test undo status in unsafe directory."""
        with patch.object(undo_service, "is_safe_for_undo", return_value=(False, "System directory")):
            is_available, message = undo_service.get_undo_status(mock_session)
            assert not is_available
            assert message == "Disabled (system directory)"

    def test_get_undo_status_not_initialized(self, mock_session, tmp_path):
        """Test undo status when Git not initialized."""
        fresh_session_dir = tmp_path / "status" / ".sidekick" / "sessions" / "test-session-123"
        fresh_session_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=fresh_session_dir):
            with patch.object(undo_service, "is_safe_for_undo", return_value=(True, "Safe")):
                is_available, message = undo_service.get_undo_status(mock_session)
                assert not is_available
                assert message == "Not initialized"

    def test_get_undo_status_no_commits(self, mock_session, mock_session_dir):
        """Test undo status with only initial commit."""
        (mock_session_dir / ".git").mkdir()
        mock_result = Mock(stdout="abc123")
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch.object(undo_service, "is_safe_for_undo", return_value=(True, "Safe")):
                with patch("sidekick.services.undo_service.subprocess.run", return_value=mock_result) as mock_run:
                    is_available, message = undo_service.get_undo_status(mock_session)
                    assert is_available
                    assert message == "Available (no changes to undo)"

    def test_get_undo_status_with_commits(self, mock_session, mock_session_dir):
        """Test undo status with multiple commits."""
        (mock_session_dir / ".git").mkdir()
        mock_result = Mock(stdout="abc123\ndef456\nghi789")
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch.object(undo_service, "is_safe_for_undo", return_value=(True, "Safe")):
                with patch("sidekick.services.undo_service.subprocess.run", return_value=mock_result):
                    is_available, message = undo_service.get_undo_status(mock_session)
                    assert is_available
                    assert message == "Available (2 commits to undo)"

    def test_get_undo_status_git_error(self, mock_session, mock_session_dir):
        """Test undo status when Git command fails."""
        (mock_session_dir / ".git").mkdir()
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch.object(undo_service, "is_safe_for_undo", return_value=(True, "Safe")):
                with patch("sidekick.services.undo_service.subprocess.run", side_effect=Exception("Git error")):
                    is_available, message = undo_service.get_undo_status(mock_session)
                    assert not is_available
                    assert message == "Error checking status"


class TestGitInitialization:
    """Test Git repository initialization."""

    def test_init_undo_system_already_exists(self, mock_session, mock_session_dir):
        """Test initialization when already initialized."""
        (mock_session_dir / ".git").mkdir()
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run") as mock_run:
                result = undo_service.init_undo_system(mock_session)
                assert result is True
                assert mock_run.call_count == 0  # Should not call git when already exists

    def test_init_undo_system_success(self, mock_session, tmp_path):
        """Test successful Git initialization."""
        fresh_session_dir = tmp_path / "success" / ".sidekick" / "sessions" / "test-session-123"
        fresh_session_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=fresh_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run") as mock_run:
                mock_run.return_value = Mock()
                result = undo_service.init_undo_system(mock_session)
                assert result is True
                assert mock_run.call_count == 3

    def test_init_undo_system_timeout(self, mock_session, tmp_path):
        """Test initialization timeout handling."""
        # Create a fresh session dir without .git
        fresh_session_dir = tmp_path / "fresh" / ".sidekick" / "sessions" / "test-session-123"
        fresh_session_dir.mkdir(parents=True, exist_ok=True)
        
        # Double check .git doesn't exist  
        assert not (fresh_session_dir / ".git").exists()
            
        with patch("sidekick.services.undo_service.get_session_dir", return_value=fresh_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 5)) as mock_run:
                result = undo_service.init_undo_system(mock_session)
                assert mock_run.called  # Verify subprocess.run was called
                assert result is False

    def test_init_undo_system_error(self, mock_session, tmp_path):
        """Test initialization error handling."""
        fresh_session_dir = tmp_path / "error" / ".sidekick" / "sessions" / "test-session-123"
        fresh_session_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=fresh_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run", side_effect=Exception("Git error")):
                result = undo_service.init_undo_system(mock_session)
                assert result is False


class TestCommitOperations:
    """Test Git commit operations."""

    def test_commit_for_undo_no_session(self):
        """Test commit without session raises error."""
        with pytest.raises(ValueError, match="session is required"):
            undo_service.commit_for_undo("test")

    def test_commit_for_undo_not_initialized(self, mock_session, tmp_path):
        """Test commit when Git not initialized."""
        # Ensure .git directory doesn't exist
        fresh_session_dir = tmp_path / "commit" / ".sidekick" / "sessions" / "test-session-123"
        fresh_session_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=fresh_session_dir):
            result = undo_service.commit_for_undo("test", mock_session)
            assert result is False

    def test_commit_for_undo_success(self, mock_session, mock_session_dir):
        """Test successful commit operation."""
        (mock_session_dir / ".git").mkdir()
        mock_result = Mock(stdout="", stderr="")
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run", return_value=mock_result):
                with patch("time.strftime", return_value="2024-01-01 12:00:00"):
                    result = undo_service.commit_for_undo("test operation", mock_session)
                    assert result is True

    def test_commit_for_undo_nothing_to_commit(self, mock_session, mock_session_dir):
        """Test commit with no changes."""
        (mock_session_dir / ".git").mkdir()
        mock_result = Mock(stdout="nothing to commit", stderr="")
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run", return_value=mock_result):
                result = undo_service.commit_for_undo("test", mock_session)
                assert result is False

    def test_commit_for_undo_timeout(self, mock_session, mock_session_dir):
        """Test commit timeout handling."""
        (mock_session_dir / ".git").mkdir()
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 5)):
                result = undo_service.commit_for_undo("test", mock_session)
                assert result is False


class TestRollbackFunctionality:
    """Test undo/rollback operations."""

    def test_perform_undo_not_initialized(self, mock_session, tmp_path):
        """Test undo when Git not initialized."""
        # Ensure .git directory doesn't exist
        fresh_session_dir = tmp_path / "undo" / ".sidekick" / "sessions" / "test-session-123"
        fresh_session_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=fresh_session_dir):
            success, message = undo_service.perform_undo(mock_session)
            assert not success
            assert message == "Undo system not initialized"

    def test_perform_undo_nothing_to_undo(self, mock_session, mock_session_dir):
        """Test undo with only initial commit."""
        (mock_session_dir / ".git").mkdir()
        mock_result = Mock(stdout="abc123")
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run", return_value=mock_result):
                success, message = undo_service.perform_undo(mock_session)
                assert not success
                assert message == "Nothing to undo"

    def test_perform_undo_success(self, mock_session, mock_session_dir):
        """Test successful undo operation."""
        (mock_session_dir / ".git").mkdir()
        mock_log_result = Mock(stdout="abc123\ndef456")
        mock_msg_result = Mock(stdout="test operation - 2024-01-01 12:00:00")
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run") as mock_run:
                mock_run.side_effect = [mock_log_result, mock_msg_result, Mock()]
                success, message = undo_service.perform_undo(mock_session)
                
                assert success
                assert message == "Successfully undid last change"
                assert len(mock_session.messages) == 1
                assert "last changes were undone" in mock_session.messages[0].parts[0].content

    def test_perform_undo_timeout(self, mock_session, mock_session_dir):
        """Test undo timeout handling."""
        (mock_session_dir / ".git").mkdir()
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 5)):
                success, message = undo_service.perform_undo(mock_session)
                assert not success
                assert "timed out" in message

    def test_perform_undo_error(self, mock_session, mock_session_dir):
        """Test undo error handling."""
        (mock_session_dir / ".git").mkdir()
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run", side_effect=Exception("Git error")):
                success, message = undo_service.perform_undo(mock_session)
                assert not success
                assert "Error performing undo" in message


class TestAsyncOperations:
    """Test async subprocess handling."""

    def test_subprocess_timeout_handling(self, mock_session, mock_session_dir):
        """Test proper timeout handling in subprocess calls."""
        (mock_session_dir / ".git").mkdir()
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run") as mock_run:
                undo_service.get_undo_status(mock_session)
                
                args, kwargs = mock_run.call_args
                assert kwargs.get("timeout") == 5

    def test_subprocess_output_capture(self, mock_session, mock_session_dir):
        """Test subprocess output capture configuration."""
        (mock_session_dir / ".git").mkdir()
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run") as mock_run:
                mock_run.return_value = Mock(stdout="test")
                undo_service.get_undo_status(mock_session)
                
                args, kwargs = mock_run.call_args
                assert kwargs.get("capture_output") is True
                assert kwargs.get("text") is True


class TestErrorRecovery:
    """Test error recovery mechanisms."""

    def test_git_operation_error_formatting(self):
        """Test GitOperationError message formatting."""
        original = Exception("Permission denied")
        error = GitOperationError("commit", "Failed to commit changes", original)
        assert str(error) == "Git commit failed: Failed to commit changes"
        assert error.operation == "commit"
        assert error.original_error == original

    def test_empty_undo_stack_message(self, mock_session, mock_session_dir):
        """Test appropriate message for empty undo stack."""
        (mock_session_dir / ".git").mkdir()
        mock_result = Mock(stdout="abc123")
        
        with patch("sidekick.services.undo_service.get_session_dir", return_value=mock_session_dir):
            with patch("sidekick.services.undo_service.subprocess.run", return_value=mock_result):
                success, message = undo_service.perform_undo(mock_session)
                assert not success
                assert message == "Nothing to undo"