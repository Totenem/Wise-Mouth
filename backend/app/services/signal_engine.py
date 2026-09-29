"""Hybrid signal engine: rules nominate -> LLM refines -> state connects over time."""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

from ..schemas.events import Signal, Utterance
from . import rules
from .conversation_state import ConversationState, Event

log = logging.getLogger("wisemouth.engine")
Emit = Callable[[str, Signal], Awaitable[None]]


class SignalEngine:
    def __init__(self, llm, emit: Emit):
        self.llm = llm
        self.emit = emit
        self.state = ConversationState(judge=llm if getattr(llm, "enabled", False) else None)
        self._lock = asyncio.Lock()

    async def _publish(self, events: list[Event]) -> None:
        for kind, sig in events:
            await self.emit(kind, sig)

    async def ingest_utterance(self, utt: Utterance) -> None:
        """The single entry point for live audio, typed text and demo mode."""
        async with self._lock:
            try:
                facts = rules.analyze(utt.text)
                if facts and self.llm is not None:
                    facts = await self.llm.refine(facts, utt, self.state.utterances)
                await self._publish(await self.state.process(utt, facts))
            except Exception:
                log.exception("engine failure on %r", utt.text)

    async def sweep(self, now_ms: int) -> None:
        async with self._lock:
            await self._publish(self.state.sweep(now_ms))

    async def flush(self) -> None:
        async with self._lock:
            await self._publish(self.state.flush())
