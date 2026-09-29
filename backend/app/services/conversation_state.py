"""Per-room conversation state and temporal intelligence.

Pure logic: consumes (utterance, facts) and returns events. The only async
dependency is an optional `Judge` used for semantic checks when heuristics are
inconclusive.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Literal, Protocol

from ..config import settings
from ..schemas.events import Ref, Signal, SignalType, Utterance
from .rules import Fact
from .text_utils import content_tokens, overlap, tokens_match

EventKind = Literal["signal", "signal_update"]
Event = tuple[EventKind, Signal]

ANSWER_START = re.compile(r"^(?:yes|yeah|yep|no|nope|sure|i can|i'll|i will|we can|i think (?:it|we|that)|it's|it is)\b", re.I)


class Judge(Protocol):
    async def weakens(self, commitment_text: str, utterance_text: str) -> bool | None: ...
    async def answers(self, question: str, reply: str) -> bool | None: ...


def _id() -> str:
    return uuid.uuid4().hex[:10]


@dataclass
class Commitment:
    id: str
    speaker: str
    action: str
    text: str
    tokens: list[str]
    ts: int
    status: str = "active"  # active | changed
    changed_ts: int | None = None


@dataclass
class PendingQuestion:
    id: str
    speaker: str
    text: str
    tokens: list[str]
    ts: int
    others_seen: int = 0
    signal: Signal | None = None  # set once flagged unanswered


@dataclass
class ConcernTopic:
    tokens: list[str]
    mentions: list[tuple[str, str, int]] = field(default_factory=list)  # speaker,text,ts
    signal: Signal | None = None


@dataclass
class Position:
    speaker: str
    text: str
    options: list[str]
    tokens: list[str]
    ts: int
    idx: int


class ConversationState:
    def __init__(self, judge: Judge | None = None):
        self.judge = judge
        self.utterances: list[Utterance] = []
        self.signals: dict[str, Signal] = {}
        self.commitments: list[Commitment] = []
        self.questions: list[PendingQuestion] = []
        self.concerns: list[ConcernTopic] = []
        self.positions: list[Position] = []
        self.open_disagreements: list[Signal] = []

    # ---- helpers ----------------------------------------------------------
    def _emit(self, events: list[Event], sig: Signal) -> Signal:
        self.signals[sig.id] = sig
        events.append(("signal", sig))
        return sig

    def _update(self, events: list[Event], sig: Signal) -> None:
        self.signals[sig.id] = sig
        events.append(("signal_update", sig))

    def _floor(self, f: Fact) -> bool:
        return f.confidence >= settings.min_signal_confidence

    # ---- main entry -------------------------------------------------------
    async def process(self, utt: Utterance, facts: list[Fact]) -> list[Event]:
        events: list[Event] = []
        idx = len(self.utterances)
        self.utterances.append(utt)
        kinds = {f.kind for f in facts}

        await self._check_answers(utt, "commitment" in kinds, "question" in kinds, events)

        for f in facts:
            if f.kind in ("uncertainty", "hedging") and self._floor(f):
                self._simple(events, utt, f)
            elif f.kind == "commitment" and self._floor(f):
                self._commitment(events, utt, f)
            elif f.kind == "weaken":
                await self._weaken(events, utt, f)
            elif f.kind == "question":
                self._question(utt, f)
            elif f.kind == "concern":
                self._concern(events, utt, f)
            elif f.kind == "position":
                self._position(events, utt, f, idx)
            elif f.kind == "disagree":
                self._explicit_disagree(events, utt, f)
            elif f.kind == "decision":
                self._decision(events, utt)
        return events

    # ---- simple per-utterance signals --------------------------------------
    def _simple(self, events, utt: Utterance, f: Fact) -> None:
        kind = SignalType(f.kind)
        if kind == SignalType.uncertainty:
            summary = f'{utt.speaker} used uncertainty language: low-commitment wording detected.'
        else:
            summary = f"{utt.speaker}'s wording agrees or proposes, but commitment strength appears low based on language."
        self._emit(events, Signal(
            id=_id(), type=kind, speaker=utt.speaker, evidence=f.sentence,
            timestamp_ms=utt.start_ms, confidence=round(f.confidence, 2), summary=summary,
            topic=" ".join(content_tokens(f.sentence)[:3]) or None,
        ))

    def _commitment(self, events, utt: Utterance, f: Fact) -> None:
        action = f.extra.get("action") or f.sentence
        c = Commitment(_id(), utt.speaker, action, f.sentence, content_tokens(action), utt.start_ms)
        self.commitments.append(c)
        self._emit(events, Signal(
            id=c.id, type=SignalType.commitment, speaker=utt.speaker, evidence=f.sentence,
            timestamp_ms=utt.start_ms, confidence=round(f.confidence, 2),
            summary=f"{utt.speaker} made a commitment: {action}.", topic=action,
            meta={"action": action},
        ))

    # ---- commitment change -------------------------------------------------
    async def _weaken(self, events, utt: Utterance, f: Fact) -> None:
        mine = [c for c in self.commitments if c.speaker == utt.speaker and c.status == "active"]
        if not mine:
            return
        toks = content_tokens(f.sentence)
        scored = sorted(((overlap(c.tokens, toks), c.ts, c) for c in mine), key=lambda t: (t[0], t[1]), reverse=True)
        best_overlap, _, target = scored[0]
        confidence = 0.92 if best_overlap else 0.7
        if not best_overlap and len(mine) > 1 and self.judge is None:
            return  # ambiguous and nothing to disambiguate with
        if not best_overlap and self.judge is not None:
            verdict = await self.judge.weakens(target.text, f.sentence)
            if verdict is False:
                return
            if verdict is True:
                confidence = 0.85
        target.status = "changed"
        target.changed_ts = utt.start_ms
        self._emit(events, Signal(
            id=_id(), type=SignalType.commitment_change, speaker=utt.speaker, evidence=f.sentence,
            timestamp_ms=utt.start_ms, confidence=confidence, topic=target.action,
            summary=f"{utt.speaker} previously committed to {target.action.lower()}; later language weakens that commitment.",
            related=Ref(speaker=target.speaker, text=target.text, timestamp_ms=target.ts),
            meta={"pattern": "commitment -> weakened commitment", "commitment_id": target.id},
        ))

    # ---- questions ----------------------------------------------------------
    def _question(self, utt: Utterance, f: Fact) -> None:
        self.questions.append(PendingQuestion(_id(), utt.speaker, f.sentence, content_tokens(f.sentence), utt.start_ms))

    async def _is_answer(self, q: PendingQuestion, utt: Utterance, is_commit: bool, is_q: bool) -> bool:
        if utt.speaker == q.speaker or is_q:
            return False
        if is_commit or ANSWER_START.match(utt.text.strip()):
            return True
        if overlap(q.tokens, content_tokens(utt.text)) >= 1:
            return True
        if self.judge is not None:
            return bool(await self.judge.answers(q.text, utt.text))
        return False

    async def _check_answers(self, utt: Utterance, is_commit: bool, is_q: bool, events) -> None:
        for q in list(self.questions):
            if utt.speaker == q.speaker:
                continue
            if await self._is_answer(q, utt, is_commit, is_q):
                if q.signal is not None:
                    q.signal.status = "resolved"
                    self._update(events, q.signal)
                self.questions.remove(q)
                continue
            if not is_q:
                q.others_seen += 1
            if q.signal is None and q.others_seen >= settings.unanswered_after_utterances:
                self._flag_unanswered(events, q)

    def _flag_unanswered(self, events, q: PendingQuestion) -> None:
        q.signal = Signal(
            id=q.id, type=SignalType.unanswered_question, speaker=q.speaker, evidence=q.text,
            timestamp_ms=q.ts, confidence=0.85, summary="Question asked; no response detected.",
            topic=" ".join(q.tokens[:3]) or None,
        )
        self._emit(events, q.signal)

    def sweep(self, now_ms: int) -> list[Event]:
        events: list[Event] = []
        for q in self.questions:
            if q.signal is None and now_ms - q.ts >= settings.unanswered_after_seconds * 1000:
                self._flag_unanswered(events, q)
        return events

    def flush(self) -> list[Event]:
        events: list[Event] = []
        for q in self.questions:
            if q.signal is None:
                self._flag_unanswered(events, q)
        return events

    # ---- repeated concerns ----------------------------------------------------
    def _concern(self, events, utt: Utterance, f: Fact) -> None:
        toks = content_tokens(f.sentence)
        if not toks:
            return
        topic = next((c for c in self.concerns if overlap(c.tokens, toks) >= 1), None)
        if topic is None:
            self.concerns.append(ConcernTopic(toks, [(utt.speaker, f.sentence, utt.start_ms)]))
            return
        label = next((t for t in toks if any(tokens_match(t, x) for x in topic.tokens)), toks[0])
        topic.mentions.append((utt.speaker, f.sentence, utt.start_ms))
        topic.tokens = list(dict.fromkeys(topic.tokens + toks))
        n = len(topic.mentions)
        first_speaker, first_text, first_ts = topic.mentions[0]
        summary = f"{utt.speaker} raised a concern about {label} {n} times. Topic remains unresolved."
        if topic.signal is None:
            topic.signal = Signal(
                id=_id(), type=SignalType.repeated_concern, speaker=utt.speaker, evidence=f.sentence,
                timestamp_ms=utt.start_ms, confidence=0.85, summary=summary, topic=label, count=n,
                related=Ref(speaker=first_speaker, text=first_text, timestamp_ms=first_ts),
                participants=sorted({m[0] for m in topic.mentions}),
                meta={"mentions": [{"speaker": s, "text": t, "timestamp_ms": ts} for s, t, ts in topic.mentions]},
            )
            self._emit(events, topic.signal)
        else:
            s = topic.signal
            s.count, s.summary, s.evidence, s.timestamp_ms = n, summary, f.sentence, utt.start_ms
            s.participants = sorted({m[0] for m in topic.mentions})
            s.meta = {"mentions": [{"speaker": a, "text": t, "timestamp_ms": ts} for a, t, ts in topic.mentions]}
            self._update(events, s)

    # ---- disagreement -----------------------------------------------------------
    def _open_between(self, a: str, b: str) -> Signal | None:
        return next((s for s in self.open_disagreements if {a, b} <= set(s.participants)), None)

    def _new_disagreement(self, events, utt: Utterance, other: Position | tuple, topic: str, evidence: str) -> None:
        o_speaker, o_text, o_ts = (other.speaker, other.text, other.ts) if isinstance(other, Position) else other
        if self._open_between(utt.speaker, o_speaker):
            return
        sig = Signal(
            id=_id(), type=SignalType.disagreement, speaker=utt.speaker, evidence=evidence,
            timestamp_ms=utt.start_ms, confidence=0.8, topic=topic,
            summary=f"{o_speaker} and {utt.speaker} expressed different positions. Status: no final decision detected.",
            related=Ref(speaker=o_speaker, text=o_text, timestamp_ms=o_ts),
            participants=sorted({o_speaker, utt.speaker}), meta={"status_text": "No final decision detected"},
        )
        self.open_disagreements.append(sig)
        self._emit(events, sig)

    def _position(self, events, utt: Utterance, f: Fact, idx: int) -> None:
        opts = f.extra.get("options", [])
        pos = Position(utt.speaker, f.sentence, opts, content_tokens(f.sentence), utt.start_ms, idx)
        other = next((p for p in reversed(self.positions)
                      if p.speaker != utt.speaker and idx - p.idx <= 8), None)
        self.positions.append(pos)
        if other is None:
            return
        a, b = (other.options[0] if other.options else None), (opts[0] if opts else None)
        if a and b and a.lower() == b.lower():
            return  # same option -> agreement
        topic = f"{a} vs {b}" if a and b else "competing positions"
        self._new_disagreement(events, utt, other, topic, f.sentence)

    def _explicit_disagree(self, events, utt: Utterance, f: Fact) -> None:
        prev = next((u for u in reversed(self.utterances[:-1]) if u.speaker != utt.speaker), None)
        if prev is None:
            return
        self._new_disagreement(events, utt, (prev.speaker, prev.text, prev.start_ms), "explicit disagreement", f.sentence)

    def _decision(self, events, utt: Utterance) -> None:
        for s in self.open_disagreements:
            s.status = "resolved"
            s.meta = {**s.meta, "status_text": "Decision detected", "resolved_ms": utt.start_ms}
            self._update(events, s)
        self.open_disagreements.clear()

    # ---- snapshot ------------------------------------------------------------------
    def counts(self) -> dict[str, int]:
        out = {t.value: 0 for t in SignalType}
        for s in self.signals.values():
            if s.status == "resolved" and s.type in (SignalType.unanswered_question, SignalType.disagreement):
                continue
            out[s.type.value] += 1
        return out
