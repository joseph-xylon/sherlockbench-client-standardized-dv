import pytest
from sherlockbench_openai.main import list_to_map, destructure, normalize_args

def test_destructure():
    data = {'a': 1, 'b': 2, 'c': 3}
    assert list(destructure(data, 'a', 'c')) == [1, 3]
    assert list(destructure(data, 'b')) == [2]

def test_list_to_map():
    assert list_to_map(["integer", "integer"]) == {'a': {'type': 'integer'}, 'b': {'type': 'integer'}}
    assert list_to_map(["boolean", "boolean"]) == {'a': {'type': 'boolean'}, 'b': {'type': 'boolean'}}
    assert list_to_map(["string"]) == {'a': {'type': 'string'}}

def test_normalize_args():
    assert normalize_args({'a': 1, 'b': 2, 'c': 3}) == [1, 2, 3]
