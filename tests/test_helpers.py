import sys

from rich.text import Text

from sidekick.utils.helpers import capture_stdout, ext_to_lang, key_to_title, render_file_diff


# Tests for key_to_title
def test_key_to_title_simple():
    assert key_to_title("hello_world") == "Hello World"


def test_key_to_title_with_uppercase_word():
    assert key_to_title("api_key") == "API Key"
    assert key_to_title("some_url_id") == "Some URL ID"


def test_key_to_title_single_word():
    assert key_to_title("test") == "Test"


def test_key_to_title_with_numbers():
    assert key_to_title("version_1_id") == "Version 1 ID"


def test_key_to_title_leading_underscore():
    assert key_to_title("_private_key") == " Private Key"


def test_key_to_title_trailing_underscore():
    assert key_to_title("key_value_") == "Key Value "


def test_key_to_title_mixed():
    assert key_to_title("user_id_from_api") == "User ID From API"


# Tests for ext_to_lang
def test_ext_to_lang_known():
    assert ext_to_lang("script.py") == "python"
    assert ext_to_lang("main.js") == "javascript"
    assert ext_to_lang("config.yaml") == "yaml"
    assert ext_to_lang("config.yml") == "yaml"
    assert ext_to_lang("styles.css") == "css"


def test_ext_to_lang_unknown():
    assert ext_to_lang("document.txt") == "text"
    assert ext_to_lang("archive.zip") == "text"


def test_ext_to_lang_no_extension():
    assert ext_to_lang("README") == "text"


def test_ext_to_lang_multiple_dots():
    assert (
        ext_to_lang("archive.tar.gz") == "text"
    )  # Based on the implementation, only the last part matters
    assert ext_to_lang("component.test.js") == "javascript"


def test_ext_to_lang_path_components():
    assert ext_to_lang("src/utils/helpers.py") == "python"
    assert ext_to_lang("/absolute/path/to/file.ts") == "typescript"


def test_ext_to_lang_case_sensitivity():
    # Current implementation is case-sensitive for extension mapping
    assert ext_to_lang("script.PY") == "text"


# Tests for render_file_diff
def test_render_file_diff_no_change():
    target = "line1\nline2\nline3"
    patch = "line1\nline2\nline3"
    expected = Text("  line1\n  line2\n  line3\n")
    assert render_file_diff(target, patch).plain == expected.plain


def test_render_file_diff_addition():
    target = "line1\nline3"
    patch = "line1\nline2\nline3"
    expected = Text("  line1\n+ line2\n  line3\n")
    assert render_file_diff(target, patch).plain == expected.plain


def test_render_file_diff_deletion():
    target = "line1\nline2\nline3"
    patch = "line1\nline3"
    expected = Text("  line1\n- line2\n  line3\n")
    assert render_file_diff(target, patch).plain == expected.plain


def test_render_file_diff_replacement():
    target = "line1\nold_line2\nline3"
    patch = "line1\nnew_line2\nline3"
    expected = Text("  line1\n- old_line2\n+ new_line2\n  line3\n")
    assert render_file_diff(target, patch).plain == expected.plain


def test_render_file_diff_multiple_changes():
    target = "start\nline_a\nline_b\nend"
    patch = "start\nline_x\nline_b\nline_y\nend"
    expected = Text("  start\n- line_a\n+ line_x\n  line_b\n+ line_y\n  end\n")
    assert render_file_diff(target, patch).plain == expected.plain


def test_render_file_diff_empty_target():
    target = ""
    patch = "new line1\nnew line2"
    expected = Text("+ new line1\n+ new line2\n")
    assert render_file_diff(target, patch).plain == expected.plain


def test_render_file_diff_empty_patch():
    target = "old line1\nold line2"
    patch = ""
    expected = Text("- old line1\n- old line2\n")
    assert render_file_diff(target, patch).plain == expected.plain


# Tests for capture_stdout
def test_capture_stdout_captures_print():
    original_stdout = sys.stdout
    try:
        with capture_stdout() as stdout_capture:
            print("Hello, world!")
        captured_output = stdout_capture.getvalue()
        assert captured_output == "Hello, world!\n"
    finally:
        sys.stdout = original_stdout


def test_capture_stdout_multiple_prints():
    original_stdout = sys.stdout
    try:
        with capture_stdout() as stdout_capture:
            print("First line.")
            print("Second line.")
        captured_output = stdout_capture.getvalue()
        assert captured_output == "First line.\nSecond line.\n"
    finally:
        sys.stdout = original_stdout


def test_capture_stdout_no_output():
    original_stdout = sys.stdout
    try:
        with capture_stdout() as stdout_capture:
            pass  # No output
        captured_output = stdout_capture.getvalue()
        assert captured_output == ""
    finally:
        sys.stdout = original_stdout


def test_capture_stdout_restores_stdout():
    original_stdout = sys.stdout
    with capture_stdout():
        print("This goes to the capture")
    # After the context manager, sys.stdout should be restored
    assert sys.stdout == original_stdout
    # Just to be safe, explicitly restore if the assert fails somehow before finally
    sys.stdout = original_stdout


def test_capture_stdout_exception_handling():
    original_stdout = sys.stdout
    try:
        with capture_stdout() as stdout_capture:
            print("Before exception")
            raise ValueError("Test exception")
    except ValueError:
        # Check that stdout is restored even if an exception occurs
        assert sys.stdout == original_stdout
        # Check that the output up to the exception was captured
        captured_output = stdout_capture.getvalue()
        assert captured_output == "Before exception\n"
    finally:
        # Ensure restoration even if the test logic itself had an error
        sys.stdout = original_stdout
