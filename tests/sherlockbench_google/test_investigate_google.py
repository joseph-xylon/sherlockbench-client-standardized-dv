import pytest
from google.genai import types
from sherlockbench_google.investigate import list_to_map

def test_list_to_map():
    assert list_to_map(['integer', 'integer', 'integer']) == {
        'a': types.Schema(type='INTEGER'),
        'b': types.Schema(type='INTEGER'),
        'c': types.Schema(type='INTEGER')
    }
    assert list_to_map(["boolean", "boolean"]) == {
        'a': types.Schema(type='BOOLEAN'),
        'b': types.Schema(type='BOOLEAN')
    }
    assert list_to_map(['string', 'string']) == {
        'a': types.Schema(type='STRING'),
        'b': types.Schema(type='STRING')
    }
    assert list_to_map(['string', 'integer']) == {
        'a': types.Schema(type='STRING'),
        'b': types.Schema(type='INTEGER')
    }
