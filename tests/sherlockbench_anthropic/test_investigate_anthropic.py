import pytest
from sherlockbench_anthropic.investigate import list_to_map, normalize_args, parse_completion

def test_list_to_map():
    assert list_to_map(['integer', 'integer', 'integer']) == {'a': {'type': 'integer'}, 'b': {'type': 'integer'}, 'c': {'type': 'integer'}}
    assert list_to_map(["boolean", "boolean"]) == {'a': {'type': 'boolean'}, 'b': {'type': 'boolean'}}
    assert list_to_map(['string', 'string']) == {'a': {'type': 'string'}, 'b': {'type': 'string'}}
    assert list_to_map(['string', 'integer']) == {'a': {'type': 'string'}, 'b': {'type': 'integer'}}

def test_normalize_args():
    assert normalize_args({'a': 1, 'b': 2, 'c': 3}) == [1, 2, 3]

# def test_parse_completion():
#     example_completion = [
#         {
#             "type": "text",
#             "text": "<thinking>foo bar</thinking>"
#         },
#         {
#             "type": "tool_use",
#             "id": "toolu_01A09q90qw90lq917835lq9",
#             "name": "get_weather",
#             "input": {"location": "San Francisco, CA"}
#         }
#     ]
#     assert parse_completion(example_completion) == ("<thinking>foo bar</thinking>", {"location": "San Francisco, CA"})
#     assert parse_completion([{"type": "text", "text": "foo bar"}]) == ("foo bar", None)
