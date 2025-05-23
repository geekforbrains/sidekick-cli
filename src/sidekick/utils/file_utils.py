"""
Module: sidekick.utils.file_utils

Provides file system utilities and helper classes.
Includes DotDict for dot notation access and stdout capture functionality.
"""

import io
import sys
from contextlib import contextmanager


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


@contextmanager
def capture_stdout():
    """
    Context manager to capture stdout output.

    Example:
        with capture_stdout() as stdout_capture:
            print("This will be captured")

        captured_output = stdout_capture.getvalue()

    Returns:
        StringIO object containing the captured output
    """
    stdout_capture = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = stdout_capture
    try:
        yield stdout_capture
    finally:
        sys.stdout = original_stdout
