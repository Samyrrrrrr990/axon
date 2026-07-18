import json

import httpx
import pytest

from axon.llm.providers import ProviderError, chat


def _transport(handler):
    return httpx.MockTransport(handler)


def test_openrouter_request_shape():
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "hi there"}}]})

    out = chat(
        "openrouter", "some/model:free",
        [{"role": "user", "content": "hello"}],
        settings={"keys": {"openrouter": "sk-or-123"}},
        transport=_transport(handler),
    )
    assert out["text"] == "hi there"
    assert "openrouter.ai" in captured["url"]
    assert captured["auth"] == "Bearer sk-or-123"
    assert captured["body"]["model"] == "some/model:free"


def test_missing_key_raises_helpful_error():
    with pytest.raises(ProviderError, match="[Oo]pen[Rr]outer"):
        chat("openrouter", "m", [{"role": "user", "content": "x"}], settings={"keys": {}})


def test_anthropic_request_shape():
    captured = {}

    def handler(request):
        captured["url"] = str(request.url)
        captured["key"] = request.headers.get("x-api-key")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"content": [{"type": "text", "text": "claude says hi"}]})

    out = chat(
        "anthropic", "claude-sonnet-5",
        [{"role": "system", "content": "be nice"}, {"role": "user", "content": "hello"}],
        settings={"keys": {"anthropic": "sk-ant-1"}},
        transport=_transport(handler),
    )
    assert out["text"] == "claude says hi"
    assert "anthropic.com" in captured["url"]
    assert captured["key"] == "sk-ant-1"
    assert captured["body"]["system"] == "be nice"
    assert all(m["role"] != "system" for m in captured["body"]["messages"])


def test_ollama_no_key_needed():
    def handler(request):
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "local hi"}})

    out = chat("ollama", "llama3", [{"role": "user", "content": "x"}],
               settings={"keys": {}}, transport=_transport(handler))
    assert out["text"] == "local hi"


def test_openai_tool_calls_parsed():
    def handler(request):
        return httpx.Response(200, json={
            "choices": [{"message": {
                "content": None,
                "tool_calls": [{"id": "t1", "function": {"name": "search", "arguments": '{"q": "axon"}'}}],
            }}]
        })

    out = chat("openai", "gpt-x", [{"role": "user", "content": "x"}],
               settings={"keys": {"openai": "sk-1"}},
               tools=[{"name": "search", "description": "d", "parameters": {}}],
               transport=_transport(handler))
    assert out["tool_calls"] == [{"name": "search", "arguments": {"q": "axon"}}]


def test_http_error_surfaces():
    def handler(request):
        return httpx.Response(429, json={"error": {"message": "rate limited"}})

    with pytest.raises(ProviderError, match="rate limited"):
        chat("openrouter", "m", [{"role": "user", "content": "x"}],
             settings={"keys": {"openrouter": "k"}}, transport=_transport(handler))
