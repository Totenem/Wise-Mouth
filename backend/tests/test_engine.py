import pytest

from app.schemas.events import Signal, Utterance
from app.services.demo_script import DEMO_LINES
from app.services.signal_engine import SignalEngine


class Collector:
    def __init__(self):
        self.events: list[tuple[str, Signal]] = []

    async def __call__(self, kind, sig):
        self.events.append((kind, sig.model_copy(deep=True)))


async def run(lines, flush=True):
    col = Collector()
    eng = SignalEngine(None, col)
    for i, (speaker, text) in enumerate(lines):
        await eng.ingest_utterance(Utterance(id=str(i), room="t", speaker=speaker, text=text, start_ms=i * 5000))
    if flush:
        await eng.flush()
    return eng, col


async def test_demo_script_yields_expected_signals():
    eng, col = await run([(s, t) for s, t, _ in DEMO_LINES])
    counts = eng.state.counts()
    assert counts["commitment"] == 2
    assert counts["uncertainty"] == 1
    assert counts["hedging"] == 1
    assert counts["commitment_change"] == 1
    assert counts["repeated_concern"] == 1
    assert counts["disagreement"] == 1
    assert counts["unanswered_question"] == 1


async def test_commitment_change_carries_evidence():
    eng, _ = await run([
        ("John", "I'll handle the deployment."),
        ("John", "Actually, I don't think I'll have enough time to handle the deployment."),
    ])
    (chg,) = [s for s in eng.state.signals.values() if s.type.value == "commitment_change"]
    assert chg.related.text == "I'll handle the deployment."
    assert chg.related.timestamp_ms == 0 and chg.timestamp_ms == 5000
    assert chg.speaker == "John"


async def test_other_speakers_do_not_change_commitment():
    eng, _ = await run([
        ("John", "I'll handle the deployment."),
        ("Sarah", "I don't think I'll have time to handle the deployment."),
    ])
    assert eng.state.counts()["commitment_change"] == 0


async def test_repeated_concern_updates_count():
    eng, col = await run([
        ("Maria", "I'm worried about the database migration."),
        ("Maria", "The migration could cause downtime."),
        ("Maria", "I still don't think we're ready for the migration."),
    ])
    (sig,) = [s for s in eng.state.signals.values() if s.type.value == "repeated_concern"]
    assert sig.count == 3
    assert [k for k, s in col.events if s.type.value == "repeated_concern"] == ["signal", "signal_update"]


async def test_question_answered_is_not_flagged():
    eng, _ = await run([
        ("Maria", "Who's going to handle the production migration?"),
        ("John", "I'll take the migration."),
        ("Sarah", "Sounds good."),
    ])
    assert eng.state.counts()["unanswered_question"] == 0


async def test_late_answer_resolves_unanswered():
    eng, col = await run([
        ("Maria", "Who's going to handle the production migration?"),
        ("Sarah", "Let's look at the frontend."),
        ("Sarah", "The frontend needs work."),
        ("John", "I can handle the migration."),
    ], flush=False)
    assert eng.state.counts()["unanswered_question"] == 0
    assert [k for k, _ in col.events if k == "signal_update"]


async def test_decision_resolves_disagreement():
    eng, _ = await run([
        ("Michael", "We should use PostgreSQL."),
        ("Maria", "I think MongoDB makes more sense."),
        ("Michael", "Agreed, let's go with PostgreSQL."),
    ])
    assert eng.state.counts()["disagreement"] == 0


async def test_same_option_is_agreement():
    eng, _ = await run([("Michael", "We should use PostgreSQL."), ("Maria", "I prefer PostgreSQL.")])
    assert eng.state.counts()["disagreement"] == 0
