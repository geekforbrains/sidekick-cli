"""Command parser for extracting individual commands from shell command strings."""

import shlex
from typing import List, Set


def extract_commands(command_string: str) -> List[str]:
    """
    Extract individual command names from a shell command string.

    Handles:
    - Simple commands: "ls -la" -> ["ls"]
    - Chained commands: "ls && mkdir foo" -> ["ls", "mkdir"]
    - Piped commands: "ls | grep foo" -> ["ls", "grep"]
    - Commands with semicolons: "cd /tmp; ls" -> ["cd", "ls"]

    Args:
        command_string: The full shell command string

    Returns:
        List of command names (without arguments)
    """
    commands = []

    # First, we need to handle quoted strings to avoid splitting on separators inside quotes
    # We'll use a simple state machine to track whether we're inside quotes
    parts = []
    current_part = []
    in_single_quote = False
    in_double_quote = False
    i = 0

    while i < len(command_string):
        char = command_string[i]

        # Handle quotes
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current_part.append(char)
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current_part.append(char)
        # Handle separators when not in quotes
        elif not in_single_quote and not in_double_quote:
            # Check for two-character separators
            if i + 1 < len(command_string):
                two_char = command_string[i : i + 2]
                if two_char in ["&&", "||"]:
                    if current_part:
                        parts.append("".join(current_part))
                        current_part = []
                    i += 1  # Skip the second character
                    i += 1
                    continue

            # Check for single-character separators
            if char in [";", "|"]:
                if current_part:
                    parts.append("".join(current_part))
                    current_part = []
            else:
                current_part.append(char)
        else:
            current_part.append(char)

        i += 1

    # Don't forget the last part
    if current_part:
        parts.append("".join(current_part))

    # Extract the command name from each part
    for part in parts:
        part = part.strip()
        if not part:
            continue

        try:
            # Use shlex to properly parse the command considering quotes
            tokens = shlex.split(part)
            if tokens:
                # The first token is the command name
                command = tokens[0]
                # Remove any path components to get just the command name
                command = command.split("/")[-1]
                commands.append(command)
        except ValueError:
            # If shlex parsing fails, fall back to simple split
            tokens = part.split()
            if tokens:
                command = tokens[0].split("/")[-1]
                commands.append(command)

    return commands


def is_command_allowed(command_string: str, allowed_commands: Set[str]) -> bool:
    """
    Check if all commands in a command string are allowed.

    Args:
        command_string: The full shell command string
        allowed_commands: Set of allowed command names

    Returns:
        True if all commands are allowed, False otherwise
    """
    commands = extract_commands(command_string)
    return all(cmd in allowed_commands for cmd in commands)
