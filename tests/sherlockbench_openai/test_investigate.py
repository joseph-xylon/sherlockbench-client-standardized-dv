import pytest
from sherlockbench_openai.investigate import list_to_map, normalize_args

def test_investigate():
    assert list_to_map(['integer', 'integer', 'integer']) == {'a': {'type': 'integer'}, 'b': {'type': 'integer'}, 'c': {'type': 'integer'}}
    assert list_to_map(["boolean", "boolean"]) == {'a': {'type': 'boolean'}, 'b': {'type': 'boolean'}}
    assert list_to_map(['string', 'string']) == {'a': {'type': 'string'}, 'b': {'type': 'string'}}
    assert list_to_map(['string', 'integer']) == {'a': {'type': 'string'}, 'b': {'type': 'integer'}}

def test_normalize_args():
    assert normalize_args({'a': 1, 'b': 2, 'c': 3}) == [1, 2, 3]

