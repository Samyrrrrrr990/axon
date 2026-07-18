"""One chat() call that speaks to OpenRouter, OpenAI, Anthropic, or local Ollama."""

from __future__ import annotations

import json

import httpx


class ProviderError(Exception):
    pass


KEY_HELP = {
    "openrouter": "Add your free OpenRouter key in Settings — get one at openrouter.ai/keys",
    "openai": "Add your OpenAI API key in Settings.",
    "anthropic": "Add your Anthropic API key in Settings.",
}

OPENAI_COMPAT = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
}


def _client(transport) -> httpx.Client:
    return httpx.Client(timeout=120, transport=transport)


def _http_error(resp: httpx.Response) -> ProviderError:
    try:
        detail = resp.json().get("error", {}).get("message", resp.text[:300])
    except Exception:
        detail = resp.text[:300]
    return ProviderError(f"Provider returned {resp.status_code}: {detail}")


def _openai_compat(provider, model, messages, key, json_mode, temperature, tools, transport):
    body: dict = {"model": model, "messages": messages, "temperature": temperature}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    if tools:
        body["tools"] = [
            {"type": "function", "function": {"name": t["name"], "description": t["description"],
                                              "parameters": t.get("parameters") or {"type": "object", "properties": {}}}}
            for t in tools
        ]
    headers = {"Authorization": f"Bearer {key}"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/Samyrrrrrr990/axon"
        headers["X-Title"] = "Axon"
    with _client(transport) as client:
        resp = client.post(OPENAI_COMPAT[provider], json=body, headers=headers)
    if resp.status_code != 200:
        raise _http_error(resp)
    message = resp.json()["choices"][0]["message"]
    tool_calls = None
    if message.get("tool_calls"):
        tool_calls = []
        for tc in message["tool_calls"]:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append({"name": fn.get("name"), "arguments": args})
    return {"text": message.get("content") or "", "tool_calls": tool_calls}


def _anthropic(model, messages, key, json_mode, temperature, tools, transport):
    system = "\n".join(m["content"] for m in messages if m["role"] == "system")
    convo = [m for m in messages if m["role"] != "system"]
    body: dict = {
        "model": model,
        "max_tokens": 4096,
        "messages": convo,
        "temperature": temperature,
    }
    if system:
        body["system"] = system
    if json_mode:
        body["system"] = (body.get("system", "") + "\nRespond with valid JSON only.").strip()
    if tools:
        body["tools"] = [
            {"name": t["name"], "description": t["description"],
             "input_schema": t.get("parameters") or {"type": "object", "properties": {}}}
            for t in tools
        ]
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    with _client(transport) as client:
        resp = client.post("https://api.anthropic.com/v1/messages", json=body, headers=headers)
    if resp.status_code != 200:
        raise _http_error(resp)
    text_parts, tool_calls = [], []
    for block in resp.json().get("content", []):
        if block.get("type") == "text":
            text_parts.append(block["text"])
        elif block.get("type") == "tool_use":
            tool_calls.append({"name": block["name"], "arguments": block.get("input", {})})
    return {"text": "".join(text_parts), "tool_calls": tool_calls or None}


def _ollama(model, messages, json_mode, temperature, tools, transport):
    body: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if json_mode:
        body["format"] = "json"
    if tools:
        body["tools"] = [
            {"type": "function", "function": {"name": t["name"], "description": t["description"],
                                              "parameters": t.get("parameters") or {"type": "object", "properties": {}}}}
            for t in tools
        ]
    with _client(transport) as client:
        try:
            resp = client.post("http://localhost:11434/api/chat", json=body)
        except httpx.ConnectError:
            raise ProviderError(
                "Can't reach Ollama at localhost:11434. Is Ollama running? (ollama.com to install)"
            )
    if resp.status_code != 200:
        raise _http_error(resp)
    message = resp.json().get("message", {})
    tool_calls = None
    if message.get("tool_calls"):
        tool_calls = [
            {"name": tc["function"]["name"], "arguments": tc["function"].get("arguments", {})}
            for tc in message["tool_calls"]
        ]
    return {"text": message.get("content") or "", "tool_calls": tool_calls}


def chat(
    provider: str,
    model: str,
    messages: list[dict],
    settings: dict,
    json_mode: bool = False,
    temperature: float = 0.7,
    tools: list[dict] | None = None,
    transport=None,
) -> dict:
    """Returns {"text": str, "tool_calls": [{"name", "arguments"}] | None}."""
    transport = transport if transport is not None else settings.get("_transport")
    keys = settings.get("keys", {})

    if provider in OPENAI_COMPAT:
        key = keys.get(provider)
        if not key:
            raise ProviderError(f"No {provider} API key configured. {KEY_HELP[provider]}")
        return _openai_compat(provider, model, messages, key, json_mode, temperature, tools, transport)
    if provider == "anthropic":
        key = keys.get("anthropic")
        if not key:
            raise ProviderError(f"No Anthropic API key configured. {KEY_HELP['anthropic']}")
        return _anthropic(model, messages, key, json_mode, temperature, tools, transport)
    if provider == "ollama":
        return _ollama(model, messages, json_mode, temperature, tools, transport)
    raise ProviderError(f"Unknown provider '{provider}'. Use openrouter, openai, anthropic, or ollama.")
