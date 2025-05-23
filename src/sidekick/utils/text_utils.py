import os
from typing import Set


def key_to_title(key: str, uppercase_words: Set[str] = None) -> str:
    """Convert key to title, replacing underscores with spaces and capitalizing words."""
    if uppercase_words is None:
        uppercase_words = {"api", "id", "url"}

    words = key.split("_")
    result_words = []
    for word in words:
        lower_word = word.lower()
        if lower_word in uppercase_words:
            result_words.append(lower_word.upper())
        elif word:
            result_words.append(word[0].upper() + word[1:].lower())
        else:
            result_words.append("")

    return " ".join(result_words)


def ext_to_lang(path: str) -> str:
    """Get the language from the file extension. Default to `text` if not found."""
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
