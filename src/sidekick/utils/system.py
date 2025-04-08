import fnmatch
import os
import uuid
from pathlib import Path

# Default ignore patterns if .gitignore is not found
DEFAULT_IGNORE_PATTERNS = {
    "node_modules/",
    "env/",
    "venv/",
    ".git/",
    "build/",
    "dist/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "Thumbs.db",
    ".env",
    ".venv",
    "*.egg-info",
    ".pytest_cache/",
    ".coverage",
    "htmlcov/",
    ".tox/",
    "coverage.xml",
    "*.cover",
    ".idea/",
    ".vscode/",
    "*.swp",
    "*.swo",
}


def get_sidekick_home():
    """
    Get the path to the Sidekick home directory (~/.sidekick).
    Creates it if it doesn't exist.

    Returns:
        Path: The path to the Sidekick home directory.
    """
    home = Path.home() / ".sidekick"
    home.mkdir(exist_ok=True)
    return home


def get_session_dir():
    """
    Get the path to the current session directory.

    Returns:
        Path: The path to the current session directory.
    """
    from .. import session

    session_dir = get_sidekick_home() / "sessions" / session.session_id
    session_dir.mkdir(exist_ok=True, parents=True)
    return session_dir


def _load_gitignore_patterns(filepath=".gitignore"):
    """Loads patterns from a .gitignore file."""
    patterns = set()
    try:
        # Use io.open for potentially better encoding handling, though default utf-8 is usually fine
        import io

        with io.open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line)
        # print(f"Loaded {len(patterns)} patterns from {filepath}") # Debug print (optional)
    except FileNotFoundError:
        # print(f"{filepath} not found.") # Debug print (optional)
        return None
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None
    # Always ignore .git directory contents explicitly
    patterns.add(".git/")
    return patterns


def _is_ignored(rel_path, name, patterns):
    """
    Checks if a given relative path or name matches any ignore patterns.
    Mimics basic .gitignore behavior using fnmatch.
    """
    if not patterns:
        return False

    # Ensure '.git' is always ignored
    # Check both name and if the path starts with .git/
    if name == ".git" or rel_path.startswith(".git/") or "/.git/" in rel_path:
        return True

    path_parts = rel_path.split(os.sep)

    for pattern in patterns:
        # Normalize pattern: remove trailing slash for matching, but keep track if it was there
        is_dir_pattern = pattern.endswith("/")
        match_pattern = pattern.rstrip("/") if is_dir_pattern else pattern

        # Remove leading slash for root-relative patterns matching logic
        if match_pattern.startswith("/"):
            match_pattern = match_pattern.lstrip("/")
            # Root relative: Match only if rel_path starts with pattern
            if fnmatch.fnmatch(rel_path, match_pattern) or fnmatch.fnmatch(
                rel_path, match_pattern + "/*"
            ):
                # If it was a dir pattern, ensure we are matching a dir or content within it
                if is_dir_pattern:
                    # Check if rel_path is exactly the dir or starts with the dir path + '/'
                    if rel_path == match_pattern or rel_path.startswith(match_pattern + os.sep):
                        return True
                else:  # File pattern, direct match is enough
                    return True
            # If root-relative, don't check further down the path parts
            continue

        # --- Non-root-relative patterns ---

        # Check direct filename match (e.g., '*.log', 'config.ini')
        if fnmatch.fnmatch(name, match_pattern):
            # If it's a directory pattern, ensure the match corresponds to a directory segment
            if is_dir_pattern:
                # This check happens during directory pruning in get_cwd_files primarily.
                # If checking a file path like 'a/b/file.txt' against 'b/', need path checks.
                pass  # Let path checks below handle dir content matching
            else:
                # If it's a file pattern matching the name, it's ignored.
                return True

        # Check full relative path match (e.g., 'src/*.py', 'docs/specific.txt')
        if fnmatch.fnmatch(rel_path, match_pattern):
            return True

        # Check if pattern matches intermediate directory names
        # e.g. path 'a/b/c.txt', pattern 'b' (no slash) -> ignore if 'b' matches a dir name
        # e.g. path 'a/b/c.txt', pattern 'b/' (slash) -> ignore
        # Check if any directory component matches the pattern
        # This is crucial for patterns like 'node_modules' or 'build/'
        # Match pattern against any directory part
        if (
            is_dir_pattern or "/" not in pattern
        ):  # Check patterns like 'build/' or 'node_modules' against path parts
            # Check all parts except the last one (filename) if it's not a dir pattern itself
            # If dir pattern ('build/'), check all parts.
            limit = len(path_parts) if is_dir_pattern else len(path_parts) - 1
            for i in range(limit):
                if fnmatch.fnmatch(path_parts[i], match_pattern):
                    return True
            # Also check the last part if it's potentially a directory being checked directly
            if name == path_parts[-1] and fnmatch.fnmatch(name, match_pattern):
                # This case helps match directory names passed directly during walk
                return True

    return False


def get_cwd():
    """Returns the current working directory."""
    return os.getcwd()


def get_device_id():
    """
    Get the device ID from the ~/.sidekick/device_id file.
    If the file doesn't exist, generate a new UUID and save it.

    Returns:
        str: The device ID as a string.
    """
    try:
        # Get the ~/.sidekick directory
        sidekick_home = get_sidekick_home()
        device_id_file = sidekick_home / "device_id"

        # If the file exists, read the device ID
        if device_id_file.exists():
            device_id = device_id_file.read_text().strip()
            if device_id:
                return device_id

        # If we got here, either the file doesn't exist or is empty
        # Generate a new device ID
        device_id = str(uuid.uuid4())

        # Write the device ID to the file
        device_id_file.write_text(device_id)

        return device_id
    except Exception as e:
        print(f"Error getting device ID: {e}")
        # Return a temporary device ID if we couldn't get or save one
        return str(uuid.uuid4())


def cleanup_session():
    """
    Clean up the session directory after the CLI exits.
    Removes the session directory completely.

    Returns:
        bool: True if cleanup was successful, False otherwise.
    """
    try:
        from .. import session

        # If no session ID was generated, nothing to clean up
        if session.session_id is None:
            return True

        # Get the session directory using the imported function
        session_dir = get_session_dir()

        # If the directory exists, remove it
        if session_dir.exists():
            import shutil

            shutil.rmtree(session_dir)

        return True
    except Exception as e:
        print(f"Error cleaning up session: {e}")
        return False


def list_cwd(max_depth=3):
    """
    Lists files in the current working directory up to a specified depth,
    respecting .gitignore rules or a default ignore list.

    Args:
        max_depth (int): Maximum directory depth to traverse.
                         0: only files in the current directory.
                         1: includes files in immediate subdirectories.
                         ... Default is 3.

    Returns:
        list: A sorted list of relative file paths.
    """
    ignore_patterns = _load_gitignore_patterns()
    if ignore_patterns is None:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS

    file_list = []
    start_path = "."
    # Ensure max_depth is non-negative
    max_depth = max(0, max_depth)

    for root, dirs, files in os.walk(
        start_path, topdown=True, onerror=lambda e: print(f"Error walking: {e}")
    ):
        rel_root = os.path.relpath(root, start_path)
        # Handle root case where relpath is '.'
        if rel_root == ".":
            rel_root = ""
            current_depth = 0
        else:
            # Depth is number of separators + 1
            current_depth = rel_root.count(os.sep) + 1

        # --- Depth Pruning ---
        if current_depth >= max_depth:
            dirs[:] = []

        # --- Directory Ignoring ---
        original_dirs = list(dirs)
        dirs[:] = []  # Reset dirs, only add back non-ignored ones
        for d in original_dirs:
            # Important: Check the directory based on its relative path
            dir_rel_path = os.path.join(rel_root, d) if rel_root else d
            if not _is_ignored(dir_rel_path, d, ignore_patterns):
                dirs.append(d)
            # else: # Optional debug print
            #     print(f"Ignoring dir: {dir_rel_path}")

        # --- File Processing ---
        if current_depth <= max_depth:
            for f in files:
                file_rel_path = os.path.join(rel_root, f) if rel_root else f
                if not _is_ignored(file_rel_path, f, ignore_patterns):
                    # Standardize path separators for consistency
                    file_list.append(file_rel_path.replace(os.sep, "/"))

    return sorted(file_list)
