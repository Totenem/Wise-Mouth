"""LLM client resilience: circuit breaker, model discovery, output handling (mocked HTTP)."""
import httpx

from app.config import settings
from app.services.llm import LLMClient, pick_gemini_model, pick_groq_model


def client(handler, monkeypatch, **keys):
    monkeypatch.setattr(settings, "groq_api_key", keys.get("groq", "g"))
    monkeypatch.setattr(settings, "gemini_api_key", keys.get("gemini", "m"))
    monkeypatch.setattr(settings, "llm_cache_path", "/tmp/wm_test_cache.json")
    c = LLMClient(transport=httpx.MockTransport(handler))
    c.cache = {}
    return c


async def test_404_disables_provider_and_stops_retrying(monkeypatch):
    calls = []

    def handler(req):
        calls.append(req.url.host)
        return httpx.Response(404, text="model not found")

    c = client(handler, monkeypatch)
    for i in range(5):
        assert await c.complete_json(f"prompt {i}") is None
    assert len(calls) == 2  # one attempt per provider, then both are disabled
    assert not c.enabled and c.name == "rules-only"
    assert "404" in c.status["groq"] and "model not found" in c.status["groq"]


async def test_falls_over_to_second_provider(monkeypatch):
    def handler(req):
        if req.url.host == "api.groq.com":
            return httpx.Response(404, text="nope")
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]})

    c = client(handler, monkeypatch)
    assert await c.complete_json("p") == {"ok": True}
    assert c.name.startswith("gemini")


async def test_startup_check_replaces_missing_models(monkeypatch):
    def handler(req):
        if req.url.host == "api.groq.com":
            return httpx.Response(200, json={"data": [{"id": "whisper-large-v3"}, {"id": "llama-3.1-8b-instant"}]})
        return httpx.Response(200, json={"models": [
            {"name": "models/gemini-2.5-flash", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/gemini-2.5-flash-image", "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/text-embedding-004", "supportedGenerationMethods": ["embedContent"]},
        ]})

    c = client(handler, monkeypatch)
    await c.startup_check()
    assert c.models == {"groq": "llama-3.1-8b-instant", "gemini": "gemini-2.5-flash"}
    assert c.enabled


async def test_startup_check_bad_key_disables(monkeypatch):
    c = client(lambda r: httpx.Response(401, text="invalid key"), monkeypatch)
    await c.startup_check()
    assert not c.enabled


def test_model_pickers():
    assert pick_groq_model(["llama-3.3-70b-versatile", "x"], "llama-3.3-70b-versatile") == "llama-3.3-70b-versatile"
    assert pick_groq_model(["whisper-large-v3", "meta-llama/llama-4-scout"], "gone") == "meta-llama/llama-4-scout"
    assert pick_groq_model(["whisper-large-v3"], "gone") is None
    assert pick_gemini_model(["gemini-2.0-flash-lite", "gemini-2.5-flash", "gemini-1.5-pro"], "gemini-2.0-flash") == "gemini-2.5-flash"
