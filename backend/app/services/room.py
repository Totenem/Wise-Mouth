"""Rooms: participants, broadcast, engine wiring, persistence hooks."""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
import time
import uuid
from dataclasses import dataclass, field

from fastapi import WebSocket

from ..config import settings
from ..models import db
from ..schemas.events import Signal, Utterance
from .assemblyai import AssemblyAISession
from .signal_engine import SignalEngine

log = logging.getLogger("wisemouth.room")


@dataclass
class Participant:
    name: str
    ws: WebSocket
    stt: AssemblyAISession | None = None
    muted: bool = False


@dataclass
class Room:
    id: str
    llm: object
    started: float = field(default_factory=time.monotonic)
    participants: dict[str, Participant] = field(default_factory=dict)
    transcript: list[dict] = field(default_factory=list)
    status: str = "live"
    demo_task: asyncio.Task | None = None

    def __post_init__(self):
        self.engine = SignalEngine(self.llm, self._on_signal)
        self._sweeper = asyncio.create_task(self._sweep_loop())
        db.fire(lambda s: s.merge(db.Conversation(id=self.id, title=f"Conversation {self.id}")))

    # ---- time ----
    def now_ms(self) -> int:
        return int((time.monotonic() - self.started) * 1000)

    # ---- broadcast ----
    async def broadcast(self, event: dict) -> None:
        for p in list(self.participants.values()):
            try:
                await p.ws.send_json(event)
            except Exception:
                self.participants.pop(p.name, None)

    def participant_list(self) -> list[dict]:
        return [{"name": p.name, "muted": p.muted} for p in self.participants.values()]

    def snapshot(self) -> dict:
        return {
            "type": "state_snapshot",
            "room": self.id,
            "status": self.status,
            "participants": self.participant_list(),
            "transcript": self.transcript,
            "signals": [s.model_dump(mode="json") for s in self.engine.state.signals.values()],
            "counts": self.engine.state.counts(),
            "capabilities": {"stt": bool(settings.assemblyai_api_key), "llm": getattr(self.llm, "name", "rules-only")},
        }

    # ---- transcript ----
    async def partial(self, speaker: str, text: str) -> None:
        await self.broadcast({"type": "transcript_partial", "speaker": speaker, "text": text, "start_ms": self.now_ms()})

    async def final(self, speaker: str, text: str) -> Utterance:
        utt = Utterance(id=uuid.uuid4().hex[:10], room=self.id, speaker=speaker, text=text, start_ms=self.now_ms())
        seg = {"id": utt.id, "speaker": speaker, "text": text, "start_ms": utt.start_ms}
        self.transcript.append(seg)
        await self.broadcast({"type": "transcript_final", **seg})
        db.fire(lambda s: s.merge(db.TranscriptSegment(id=utt.id, conversation_id=self.id, speaker=speaker,
                                                       text=text, timestamp_ms=utt.start_ms)))
        asyncio.create_task(self.engine.ingest_utterance(utt))  # never block transcript on analysis
        return utt

    # ---- signals ----
    async def _on_signal(self, kind: str, sig: Signal) -> None:
        payload = sig.model_dump(mode="json")
        await self.broadcast({"type": kind, "signal": payload, "counts": self.engine.state.counts()})
        db.fire(lambda s: s.merge(db.SignalRow(id=sig.id, conversation_id=self.id, type=sig.type.value,
                                               speaker=sig.speaker, evidence=sig.evidence,
                                               timestamp_ms=sig.timestamp_ms, confidence=sig.confidence,
                                               signal_metadata=payload)))

    async def _sweep_loop(self) -> None:
        while self.status == "live":
            await asyncio.sleep(3)
            await self.engine.sweep(self.now_ms())

    # ---- participants ----
    async def join(self, name: str, ws: WebSocket) -> Participant:
        base, i = name, 2
        while name in self.participants:
            name, i = f"{base} {i}", i + 1
        p = Participant(name, ws)
        if settings.assemblyai_api_key:
            async def on_partial(t, n=name): await self.partial(n, t)
            async def on_final(t, n=name): await self.final(n, t)
            async def on_error(m): await self.broadcast({"type": "error", "message": m, "source": "stt"})
            p.stt = AssemblyAISession(on_partial, on_final, on_error)
            await p.stt.start()
        self.participants[name] = p
        await ws.send_json({**self.snapshot(), "you": name})
        await self.broadcast({"type": "participants", "participants": self.participant_list()})
        return p

    async def leave(self, p: Participant) -> None:
        if p.stt:
            await p.stt.close()
        self.participants.pop(p.name, None)
        await self.broadcast({"type": "participants", "participants": self.participant_list()})

    # ---- lifecycle ----
    async def end(self) -> None:
        if self.status != "live":
            return
        if self.demo_task:
            self.demo_task.cancel()
        await asyncio.sleep(0.2)  # let in-flight analysis settle
        await self.engine.flush()
        self.status = "ended"
        state = self.engine.state
        ended = dt.datetime.now(dt.timezone.utc)

        def persist(s):
            c = s.get(db.Conversation, self.id) or db.Conversation(id=self.id)
            c.status, c.ended_at = "ended", ended
            s.merge(c)
            for cm in state.commitments:
                s.merge(db.CommitmentRow(id=cm.id, conversation_id=self.id, speaker=cm.speaker, commitment=cm.action,
                                         status=cm.status, original_timestamp=cm.ts, changed_timestamp=cm.changed_ts))
            for q in state.questions:
                s.merge(db.QuestionRow(id=q.id, conversation_id=self.id, question=q.text, speaker=q.speaker,
                                       answered=False, timestamp_ms=q.ts))
        db.fire(persist)
        await self.broadcast({**self.snapshot(), "type": "session_ended"})
        for p in list(self.participants.values()):
            if p.stt:
                await p.stt.close()


class RoomManager:
    def __init__(self, llm):
        self.llm = llm
        self.rooms: dict[str, Room] = {}

    def get_or_create(self, room_id: str) -> Room:
        room = self.rooms.get(room_id)
        if room is None:
            room = self.rooms[room_id] = Room(room_id, self.llm)
        return room
