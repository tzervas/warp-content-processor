"""Tests for the environment variable processor module."""

import pytest

from warp_content_processor.processors.env_var_processor import EnvVarProcessor


@pytest.fixture
def processor():
    """Create an environment variable processor instance."""
    return EnvVarProcessor()


def test_flatten_simple_types(processor):
    """Test flattening of simple value types."""
    assert processor._flatten_list("test") == ["test"]
    assert processor._flatten_list(123) == ["123"]
    assert processor._flatten_list(True) == ["true"]
    assert processor._flatten_list(1.234) == ["1.234"]


def test_flatten_nested_lists(processor):
    """Test flattening of nested lists."""
    nested = ["a", ["b", ["c", "d"], "e"], "f"]
    assert processor._flatten_list(nested) == ["a", "b", "c", "d", "e", "f"]


def test_flatten_dict_values(processor):
    """Test flattening of dictionary values."""
    dict_value = {"key1": "value1", "key2": ["value2", "value3"]}
    result = processor._flatten_list(dict_value)
    assert set(result) == {"key1=value1", "key2=value2", "key2=value3"}


def test_normalize_mixed_types(processor):
    """Test normalization of mixed value types."""
    data = {
        "variables": {
            "SIMPLE_STR": "value",
            "MIXED_LIST": ["a", 123, True],
            "NESTED_LIST": ["x", ["y", ["z"]]],
            "DICT_VALUE": {"key": "value"},
        }
    }

    normalized = processor.normalize_content(data)
    variables = normalized["variables"]

    assert variables["simple_str"] == "value"
    assert variables["mixed_list"] == "a 123 true"
    assert variables["nested_list"] == "x y z"
    assert variables["dict_value"] == "key=value"


def test_normalize_case_sensitivity(processor):
    """Test case normalization of variable names and values."""
    data = {
        "variables": {
            "UPPERCASE": "VALUE",
            "MixedCase": "Value",
            "lowercase": "value",
        }
    }

    normalized = processor.normalize_content(data)
    variables = normalized["variables"]

    assert all(name.islower() for name in variables.keys())
    assert all(value.islower() for value in variables.values())
    assert variables["uppercase"] == "value"
    assert variables["mixedcase"] == "value"
    assert variables["lowercase"] == "value"


def test_process_invalid_types(processor):
    """Test processing of invalid variable types."""
    content = """
variables:
  valid_str: string_value
  invalid_obj: {"complex": "object"}
  invalid_type: None
"""

    result = processor.process(content)
    assert result.is_valid
    data = result.data["variables"]

    assert data["valid_str"] == "string_value"
    # Check that the complex object is converted to string representation
    assert "complex" in data["invalid_obj"] and "object" in data["invalid_obj"]
    assert data["invalid_type"] == "None"  # Converted to string


def test_empty_and_edge_cases(processor):
    """Test handling of empty and edge case values."""
    data = {
        "variables": {
            "EMPTY_LIST": [],
            "EMPTY_DICT": {},
            "SINGLE_SPACE": " ",
            "NONE_VALUE": None,
        }
    }

    normalized = processor.normalize_content(data)
    variables = normalized["variables"]

    assert variables["empty_list"] == ""
    assert variables["empty_dict"] == ""
    assert variables["single_space"] == " "
    assert variables["none_value"] == "none"
