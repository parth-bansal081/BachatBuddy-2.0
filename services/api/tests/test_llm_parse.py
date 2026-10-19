import pytest

from bb.llm import extract_json


def test_plain_json():
    assert extract_json('{"items": []}') == {"items": []}


def test_think_block_and_fence_are_removed():
    text = '<think>hmm {not json}</think>\n```json\n{"items": [{"id": 0}]}\n```'
    assert extract_json(text) == {"items": [{"id": 0}]}


def test_text_before_json_is_ignored():
    assert extract_json('Sure! {"items": []} Hope that helps')["items"] == []


def test_no_json_raises():
    with pytest.raises(ValueError):
        extract_json("I cannot help with that")
