"""LLM client: Groq -> Gemini -> None, with cache, timeout, validation and a circuit breaker.

The LLM only *refines* rule candidates (keep/drop, label, action, confidence) and
answers narrow yes/no judgments. It never invents evidence. Every failure path
returns None so callers fall back to deterministic rule behaviour.

Misconfiguration (bad key, unknown model) disables that provider instead of
retrying on every utterance; startup_check() verifies the model against the
provider's model list and picks a valid one when the configured one is gone.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from typing import Any

import httpx

from ..config import settings
from ..schemas.events import Utterance
from .rules import Fact

log = logging.getLogger("wisemouth.llm")

SYSTEM = (
    "You analyse observable conversation language only. Never infer emotions, lies, "
    "personality or hidden intent. Respond with a single JSON object and nothing else."
)

GROQ_BASE = "https://api.groq.com/openai/v1"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Cooldowns (seconds) after a failure, by kind of failure.
COOLDOWN_CONFIG = 3600.0  # 400/401/403/404: key or model is wrong; retrying won't help
COOLDOWN_RATE = 30.0  # 429
COOLDOWN_TRANSIENT = 10.0  # 5xx / timeout / network


def pick_groq_model(ids: list[str], preferred: str) -> str | None:
    if preferred in ids:
        return preferred
    bad = re.compile(r"whisper|guard|tts|orpheus|playai|distil|embed|safeguard")
    chat = [i for i in ids if not bad.search(i)]
    for want in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-20b", "openai/gpt-oss-120b"):
        if want in chat:
            return want
    llamas = sorted(i for i in chat if "llama" in i)
    return llamas[0] if llamas else (chat[0] if chat else None)


def pick_gemini_model(names: list[str], preferred: str) -> str | None:
    if preferred in names:
        return preferred
    skip = re.compile(r"image|tts|live|audio|thinking|exp|embed|vision|robotics|computer|preview")

    def version(n: str) -> float:
        m = re.search(r"gemini-(\d+(?:\.\d+)?)", n)
        return float(m.group(1)) if m else 0.0

    flash = [n for n in names if "flash" in n and not skip.search(n)]
    plain = sorted((n for n in flash if "lite" not in n), key=lambda n: (-version(n), len(n)))
    lite = sorted((n for n in flash if "lite" in n), key=lambda n: (-version(n), len(n)))
    for group in (plain, lite):
        if group:
            return group[0]
    return None


class LLMClient:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        self.cache: dict[str, Any] = {}
        self._load_cache()
        self.models = {"groq": settings.groq_model, "gemini": settings.gemini_model}
        self.disabled_until: dict[str, float] = {}
        self.status: dict[str, str] = {}
        self.providers = self._providers()
        self.http = httpx.AsyncClient(timeout=settings.llm_timeout_s, transport=transport)

    # ---- state -------------------------------------------------------------
    def _active(self) -> list[tuple[str, Any]]:
        now = time.monotonic()
        return [(n, fn) for n, fn in self.providers if self.disabled_until.get(n, 0) <= now]

    @property
    def enabled(self) -> bool:
        return bool(self._active())

    @property
    def name(self) -> str:
        active = self._active()
        return "+".join(f"{n}:{self.models[n]}" for n, _ in active) or "rules-only"

    def _disable(self, name: str, seconds: float, reason: str) -> None:
        already = self.disabled_until.get(name, 0) > time.monotonic()
        self.disabled_until[name] = time.monotonic() + seconds
        self.status[name] = reason
        if not already:  # log once per outage, not once per utterance
            log.warning("LLM %s disabled for %ds: %s", name, int(seconds), reason)

    def _providers(self):
        order = [settings.llm_provider, "gemini" if settings.llm_provider == "groq" else "groq"]
        out = []
        for p in order:
            if p == "groq" and settings.groq_api_key:
                out.append(("groq", self._groq))
            elif p == "gemini" and settings.gemini_api_key:
                out.append(("gemini", self._gemini))
        return out

    # ---- cache -----------------------------------------------------------
    def _load_cache(self):
        try:
            with open(settings.llm_cache_path, encoding="utf-8") as f:
                self.cache = json.load(f)
        except Exception:
            self.cache = {}

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(settings.llm_cache_path) or ".", exist_ok=True)
            with open(settings.llm_cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f)
        except Exception as e:  # cache is best-effort
            log.warning("cache save failed: %s", e)

    # ---- startup verification --------------------------------------------------
    async def startup_check(self) -> None:
        """Verify keys and models against each provider's model list; fix or disable."""
        for name, _ in self.providers:
            try:
                if name == "groq":
                    r = await self.http.get(f"{GROQ_BASE}/models", headers={"Authorization": f"Bearer {settings.groq_api_key}"})
                    r.raise_for_status()
                    ids = [m["id"] for m in r.json().get("data", [])]
                    chosen = pick_groq_model(ids, self.models["groq"])
                else:
                    r = await self.http.get(f"{GEMINI_BASE}/models", params={"pageSize": 200},
                                            headers={"x-goog-api-key": settings.gemini_api_key})
                    r.raise_for_status()
                    ids = [m["name"].removeprefix("models/") for m in r.json().get("models", [])
                           if "generateContent" in m.get("supportedGenerationMethods", [])]
                    chosen = pick_gemini_model(ids, self.models["gemini"])
            except httpx.HTTPStatusError as e:
                self._disable(name, COOLDOWN_CONFIG, f"model list failed: HTTP {e.response.status_code} {e.response.text[:200]}")
                continue
            except Exception as e:
                log.warning("LLM %s startup check inconclusive (%s); will try on demand", name, e.__class__.__name__)
                continue
            if chosen is None:
                self._disable(name, COOLDOWN_CONFIG, "no usable chat model available to this key")
            else:
                if chosen != self.models[name]:
                    log.warning("LLM %s: configured model %r unavailable; using %r", name, self.models[name], chosen)
                    self.models[name] = chosen
                self.status[name] = f"ok ({chosen})"
                log.info("LLM %s ready: %s", name, chosen)

    # ---- providers --------------------------------------------------------
    async def _groq(self, prompt: str) -> str:
        r = await self.http.post(
            f"{GROQ_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": self.models["groq"],
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    async def _gemini(self, prompt: str) -> str:
        r = await self.http.post(
            f"{GEMINI_BASE}/models/{self.models['gemini']}:generateContent",
            headers={"x-goog-api-key": settings.gemini_api_key},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
            },
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    async def complete_json(self, prompt: str) -> dict | None:
        key = hashlib.sha1(prompt.encode()).hexdigest()
        if key in self.cache:
            return self.cache[key]
        for name, fn in self._active():
            try:
                raw = await asyncio.wait_for(fn(prompt), settings.llm_timeout_s + 0.5)
                data = json.loads(raw)
                if isinstance(data, dict):
                    self.cache[key] = data
                    self._save_cache()
                    self.status[name] = f"ok ({self.models[name]})"
                    return data
            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                detail = f"HTTP {code} {e.response.text[:200]}"
                cooldown = COOLDOWN_RATE if code == 429 else COOLDOWN_TRANSIENT if code >= 500 else COOLDOWN_CONFIG
                self._disable(name, cooldown, detail)
            except (asyncio.TimeoutError, httpx.TransportError) as e:
                self._disable(name, COOLDOWN_TRANSIENT, f"{e.__class__.__name__}")
            except Exception as e:  # bad JSON / unexpected shape: skip this call only
                log.warning("LLM %s returned unusable output: %s", name, e.__class__.__name__)
        return None

    # ---- tasks --------------------------------------------------------------
    async def refine(self, facts: list[Fact], utt: Utterance, context: list[Utterance]) -> list[Fact]:
        """Return facts filtered/refined by the LLM; unchanged if the LLM is unavailable."""
        kinds = ("uncertainty", "hedging", "commitment", "concern", "position")
        candidates = [(i, f) for i, f in enumerate(facts) if f.kind in kinds]
        if not self.enabled or not candidates:
            return facts
        if all(f.kind in ("uncertainty", "hedging") and f.confidence >= 0.8 for _, f in candidates):
            return facts  # fast path: high-confidence lexical hits skip the LLM
        ctx = "\n".join(f"{u.speaker}: {u.text}" for u in context[-6:])
        items = "\n".join(f'{i}. kind={f.kind} sentence="{f.sentence}"' for i, f in candidates)
        prompt = (
            "Context (earlier utterances):\n" + ctx + f'\n\nCurrent utterance by {utt.speaker}: "{utt.text}"\n\n'
            "Rule-based candidates:\n" + items + "\n\n"
            "For each candidate decide if the wording really shows that pattern.\n"
            "uncertainty = speaker signals doubt; hedging = agreement/proposal with weakened commitment; "
            "commitment = speaker takes on an action; concern = speaker raises a worry/risk; "
            "position = speaker states a preferred option.\n"
            'Return {"results":[{"id":<int>,"keep":<bool>,"type":"<same, or uncertainty|hedging>",'
            '"action":"<short action, commitments only>","confidence":<0..1>}]}'
        )
        data = await self.complete_json(prompt)
        if not data:
            return facts
        by_id = {r.get("id"): r for r in data.get("results", []) if isinstance(r, dict)}
        out: list[Fact] = []
        for i, f in enumerate(facts):
            r = by_id.get(i)
            if r is None:
                out.append(f)
                continue
            if r.get("keep") is False:
                continue
            if f.kind in ("uncertainty", "hedging") and r.get("type") in ("uncertainty", "hedging"):
                f.kind = r["type"]
            if f.kind == "commitment" and isinstance(r.get("action"), str) and r["action"].strip():
                f.extra["action"] = r["action"].strip()
            if isinstance(r.get("confidence"), (int, float)):
                f.confidence = max(0.0, min(1.0, float(r["confidence"])))
            out.append(f)
        return out

    async def weakens(self, commitment_text: str, utterance_text: str) -> bool | None:
        if not self.enabled:
            return None
        data = await self.complete_json(
            f'Earlier commitment: "{commitment_text}"\nLater statement by the same person: "{utterance_text}"\n'
            'Does the later statement retract or weaken that commitment? Return {"weakens": <bool>}'
        )
        return data.get("weakens") if data and isinstance(data.get("weakens"), bool) else None

    async def answers(self, question: str, reply: str) -> bool | None:
        if not self.enabled:
            return None
        data = await self.complete_json(
            f'Question: "{question}"\nReply from a different person: "{reply}"\n'
            'Does the reply answer or directly respond to the question? Return {"answers": <bool>}'
        )
        return data.get("answers") if data and isinstance(data.get("answers"), bool) else None
