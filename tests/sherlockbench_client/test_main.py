import pytest
from sherlockbench_client.main import destructure

def test_destructure():
    data = {'a': 1, 'b': 2, 'c': 3}
    assert list(destructure(data, 'a', 'c')) == [1, 3]
    assert list(destructure(data, 'b')) == [2]
