from src.sidekick.config import deep_merge_dicts


def test_simple_merge():
    """Test merging simple dictionaries."""
    base = {"a": 1, "b": 2}
    update = {"b": 3, "c": 4}

    result = deep_merge_dicts(base, update)

    assert result == {"a": 1, "b": 3, "c": 4}


def test_nested_dict_merge():
    """Test merging nested dictionaries."""
    base = {"settings": {"allowed_tools": ["read_file"], "allowed_commands": ["ls", "cat"]}}
    update = {"settings": {"allowed_commands": ["grep", "pwd"], "custom_field": "value"}}

    result = deep_merge_dicts(base, update)

    assert result == {
        "settings": {
            "allowed_tools": ["read_file"],
            "allowed_commands": ["grep", "pwd"],
            "custom_field": "value",
        }
    }


def test_deep_nested_merge():
    """Test merging deeply nested structures."""
    base = {"a": {"b": {"c": 1, "d": 2}, "e": 3}}
    update = {"a": {"b": {"c": 10, "f": 4}, "g": 5}}

    result = deep_merge_dicts(base, update)

    assert result == {"a": {"b": {"c": 10, "d": 2, "f": 4}, "e": 3, "g": 5}}


def test_list_override():
    """Test that lists are overridden, not merged."""
    base = {"items": [1, 2, 3]}
    update = {"items": [4, 5]}

    result = deep_merge_dicts(base, update)

    assert result == {"items": [4, 5]}


def test_mixed_types_override():
    """Test that mixed types result in override."""
    base = {"field": {"nested": "value"}}
    update = {"field": "string"}

    result = deep_merge_dicts(base, update)

    assert result == {"field": "string"}


def test_empty_dicts():
    """Test merging with empty dictionaries."""
    assert deep_merge_dicts({}, {}) == {}
    assert deep_merge_dicts({"a": 1}, {}) == {"a": 1}
    assert deep_merge_dicts({}, {"b": 2}) == {"b": 2}


def test_none_values():
    """Test handling of None values."""
    base = {"a": 1, "b": None}
    update = {"b": 2, "c": None}

    result = deep_merge_dicts(base, update)

    assert result == {"a": 1, "b": 2, "c": None}


def test_preserves_update_values():
    """Test that update values always take precedence."""
    base = {"env": {"API_KEY": "default-key", "OTHER_KEY": "default-other"}}
    update = {"env": {"API_KEY": "user-key"}}

    result = deep_merge_dicts(base, update)

    assert result["env"]["API_KEY"] == "user-key"
    assert result["env"]["OTHER_KEY"] == "default-other"
