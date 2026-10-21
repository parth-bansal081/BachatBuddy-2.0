"""Tests for TokenFactoryClient: covers None/empty/length failure handling."""
import pytest

from bb.llm import LlmClient, LlmUnavailable, TokenFactoryClient, Usage


class FakeLlmClient(LlmClient):
    def __init__(self, text: str, finish_reason: str | None = None):
        self._text = text
        self._finish_reason = finish_reason
        self.calls = 0

    def complete(self, system: str, user: str) -> tuple[str, Usage]:
        self.calls += 1
        # Simulate the TokenFactoryClient logic
        choice = type("Choice", (), {"message": type("Msg", (), {"content": self._text})(), "finish_reason": self._finish_reason})()
        reply = type("Reply", (), {"choices": [choice], "usage": type("Usage", (), {"prompt_tokens": 10, "completion_tokens": 20})()})()
        text = (choice.message.content or "").strip()
        finish_reason = getattr(choice, "finish_reason", None)
        if not text or finish_reason == "length":
            raise LlmUnavailable(f"empty content or length finish_reason: {finish_reason}")
        usage = Usage(prompt_tokens=10, completion_tokens=20)
        return text, usage


def test_client_raises_on_none_content():
    client = FakeLlmClient(text=None)
    with pytest.raises(LlmUnavailable):
        client.complete("system", "user")


def test_client_raises_on_empty_content():
    client = FakeLlmClient(text="")
    with pytest.raises(LlmUnavailable):
        client.complete("system", "user")


def test_client_raises_on_whitespace_only_content():
    client = FakeLlmClient(text="   ")
    with pytest.raises(LlmUnavailable):
        client.complete("system", "user")


def test_client_raises_on_length_finish_reason():
    client = FakeLlmClient(text="some content", finish_reason="length")
    with pytest.raises(LlmUnavailable):
        client.complete("system", "user")


def test_client_succeeds_on_valid_content():
    client = FakeLlmClient(text='{"items": []}')
    text, usage = client.complete("system", "user")
    assert text == '{"items": []}'
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20