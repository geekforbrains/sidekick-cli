
from sidekick.utils.helpers import key_to_title, ext_to_lang

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
    assert ext_to_lang("archive.tar.gz") == "text" # Based on the implementation, only the last part matters
    assert ext_to_lang("component.test.js") == "javascript"

def test_ext_to_lang_path_components():
    assert ext_to_lang("src/utils/helpers.py") == "python"
    assert ext_to_lang("/absolute/path/to/file.ts") == "typescript"

def test_ext_to_lang_case_sensitivity():
    # Current implementation is case-sensitive for extension mapping
    assert ext_to_lang("script.PY") == "text"


