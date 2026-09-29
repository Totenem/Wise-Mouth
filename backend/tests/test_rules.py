import pytest

from app.services.rules import analyze


def kinds(text):
    return [f.kind for f in analyze(text)]


@pytest.mark.parametrize("text,expected", [
    ("I'm not sure we're actually ready for Friday.", "uncertainty"),
    ("Maybe we can ship on Friday.", "uncertainty"),
    ("Yeah, I guess that could work for the timeline.", "hedging"),
    ("I suppose that's fine.", "hedging"),
    ("I'll handle the deployment.", "commitment"),
    ("I'm going to finish the API today.", "commitment"),
    ("Actually, I don't think I'll have enough time to handle the deployment.", "weaken"),
    ("Who's going to handle the migration?", "question"),
    ("I'm still concerned about authentication.", "concern"),
    ("We should use PostgreSQL.", "position"),
    ("I disagree with that.", "disagree"),
    ("Let's go with PostgreSQL.", "decision"),
])
def test_detects(text, expected):
    assert expected in kinds(text)


def test_weakened_sentence_is_not_a_commitment():
    assert "commitment" not in kinds("I don't think I'll be able to finish it.")


def test_plain_statement_has_no_facts():
    assert analyze("The build finished at noon.") == []


def test_weak_markers_alone_stay_below_threshold():
    (f,) = analyze("I think it is fine")
    assert f.kind == "uncertainty" and f.confidence < 0.6


def test_commitment_action_extracted():
    (f,) = [f for f in analyze("I'll prepare the deployment checklist.") if f.kind == "commitment"]
    assert f.extra["action"] == "Prepare the deployment checklist"
