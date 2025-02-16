import pytest
from sherlockbench_google.verify import trim_to_json

def test_trim_to_json():
    assert trim_to_json('some text before { "key": "value" } some text after') == '{ "key": "value" }'

    # Multiple JSON objects (should extract only the first and last curly braces)
    assert trim_to_json('random { "a": 1 } noise { "b": 2 } more') == '{ "a": 1 } noise { "b": 2 }'

    # JSON object at the beginning
    assert trim_to_json('{ "name": "John" } some text after') == '{ "name": "John" }'

    # JSON object at the end
    assert trim_to_json('some text before { "age": 30 }') == '{ "age": 30 }'

    # Nested JSON
    assert trim_to_json('extra { "nested": { "x": 42 } } junk') == '{ "nested": { "x": 42 } }'

    # Only JSON, should remain unchanged
    assert trim_to_json('{ "only": "json" }') == '{ "only": "json" }'

    # No curly braces at all (should return empty string)
    assert trim_to_json('no json here') == ''

    # Curly braces but no valid content (should still return the braces)
    assert trim_to_json('before {} after') == '{}'

    # Multiple lines with JSON
    assert trim_to_json('Some text\n{ "multiline": true }\nExtra text') == '{ "multiline": true }'

    # Leading and trailing whitespace
    assert trim_to_json('   { "trim": true }   ') == '{ "trim": true }'
