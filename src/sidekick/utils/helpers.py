import difflib
import os

from rich.text import Text


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def key_to_title(key):
    """
    Convert key to title, replacing underscores with spaces and capitalizing words.

    Replace words found in `CAPITALIZE` with uppercase.
    """
    UPPERCASE = ["Api", "Id", "Url"]
    words = key.split("_")
    for i, word in enumerate(words):
        if word in UPPERCASE:
            words[i] = word.upper()
        else:
            words[i] = word.title()
    return " ".join(words)


def ext_to_lang(path):
    """
    Get the language from the file extension. Default to `text` if not found.
    """
    MAP = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "java": "java",
        "c": "c",
        "cpp": "cpp",
        "cs": "csharp",
        "html": "html",
        "css": "css",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
    }
    ext = os.path.splitext(path)[1][1:]
    if ext in MAP:
        return MAP[ext]
    return "text"


def render_file_diff(target: str, patch: str, colors=None) -> Text:
    """
    Create a formatted diff between target and patch text.

    Args:
        target (str): The original text to be replaced.
        patch (str): The new text to insert.
        colors (dict, optional): Dictionary containing style colors.
                                If None, no styling will be applied.

    Returns:
        Text: A Rich Text object containing the formatted diff.
    """
    # Create a clean diff with styled text
    diff_text = Text()

    # Get lines and create a diff sequence
    target_lines = target.splitlines()
    patch_lines = patch.splitlines()

    # Use difflib to identify changes
    matcher = difflib.SequenceMatcher(None, target_lines, patch_lines)

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            # Unchanged lines
            for line in target_lines[i1:i2]:
                diff_text.append(f"  {line}\n")
        elif op == "delete":
            # Removed lines - show in red with (-) prefix
            for line in target_lines[i1:i2]:
                if colors:
                    diff_text.append(f"- {line}\n", style=colors.error)
                else:
                    diff_text.append(f"- {line}\n")
        elif op == "insert":
            # Added lines - show in green with (+) prefix
            for line in patch_lines[j1:j2]:
                if colors:
                    diff_text.append(f"+ {line}\n", style=colors.success)
                else:
                    diff_text.append(f"+ {line}\n")
        elif op == "replace":
            # Removed lines with (-) prefix
            for line in target_lines[i1:i2]:
                if colors:
                    diff_text.append(f"- {line}\n", style=colors.error)
                else:
                    diff_text.append(f"- {line}\n")
            # Added lines with (+) prefix
            for line in patch_lines[j1:j2]:
                if colors:
                    diff_text.append(f"+ {line}\n", style=colors.success)
                else:
                    diff_text.append(f"+ {line}\n")

    return diff_text
