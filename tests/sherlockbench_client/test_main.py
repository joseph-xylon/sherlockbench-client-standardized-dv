import pytest
from sherlockbench_client.main import destructure, value_list_to_map

def test_destructure():
    data = {'a': 1, 'b': 2, 'c': 3}
    assert list(destructure(data, 'a', 'c')) == [1, 3]
    assert list(destructure(data, 'b')) == [2]

def test_value_list_to_map():
    assert value_list_to_map(['cat', 'dog', 'duck']) == {
        'a': 'cat',
        'b': 'dog',
        'c': 'duck'
    }

    assert value_list_to_map([8, 3, 5]) == {
        'a': 8,
        'b': 3,
        'c': 5
    }
