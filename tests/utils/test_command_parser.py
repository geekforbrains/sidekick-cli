"""Tests for command parser."""

from sidekick.ui import get_command_display_name
from sidekick.utils.command import extract_commands, is_command_allowed


def test_simple_command():
    assert extract_commands("ls -la") == ["ls"]
    assert extract_commands("mkdir -p /some/path") == ["mkdir"]
    assert extract_commands("cd /tmp") == ["cd"]


def test_commands_with_paths():
    assert extract_commands("/usr/bin/ls -la") == ["ls"]
    assert extract_commands("./scripts/deploy.sh") == ["deploy.sh"]
    assert extract_commands("/bin/bash script.sh") == ["bash"]


def test_chained_commands_with_and():
    assert extract_commands("ls && mkdir foo") == ["ls", "mkdir"]
    assert extract_commands("cd /tmp && ls -la && pwd") == ["cd", "ls", "pwd"]


def test_chained_commands_with_or():
    assert extract_commands("ls || echo 'failed'") == ["ls", "echo"]


def test_piped_commands():
    assert extract_commands("ls | grep foo") == ["ls", "grep"]
    assert extract_commands("cat file.txt | grep pattern | wc -l") == ["cat", "grep", "wc"]


def test_semicolon_separated():
    assert extract_commands("cd /tmp; ls") == ["cd", "ls"]
    assert extract_commands("echo 'hello'; echo 'world'") == ["echo", "echo"]


def test_mixed_separators():
    assert extract_commands("ls && cd /tmp; pwd | grep tmp") == ["ls", "cd", "pwd", "grep"]


def test_quoted_arguments():
    assert extract_commands('echo "hello && world"') == ["echo"]
    assert extract_commands("echo 'ls | grep'") == ["echo"]
    assert extract_commands('mkdir "my folder" && ls') == ["mkdir", "ls"]


def test_empty_and_whitespace():
    assert extract_commands("") == []
    assert extract_commands("   ") == []
    assert extract_commands("ls &&   && pwd") == ["ls", "pwd"]


def test_single_command_allowed():
    allowed = {"ls", "mkdir", "cd"}
    assert is_command_allowed("ls -la", allowed) is True
    assert is_command_allowed("rm -rf /", allowed) is False


def test_all_commands_must_be_allowed():
    allowed = {"ls", "cd"}
    assert is_command_allowed("ls && cd /tmp", allowed) is True
    assert is_command_allowed("ls && rm file", allowed) is False


def test_empty_allowed_set():
    allowed = set()
    assert is_command_allowed("ls", allowed) is False


def test_command_with_path():
    allowed = {"ls"}
    assert is_command_allowed("/usr/bin/ls", allowed) is True


def test_single_command_display():
    assert get_command_display_name("ls -la") == "'ls'"


def test_multiple_commands_display():
    assert get_command_display_name("ls && cd") == "'ls', 'cd'"
    assert get_command_display_name("cat | grep | wc") == "'cat', 'grep', 'wc'"
