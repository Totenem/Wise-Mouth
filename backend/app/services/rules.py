"""Rule-based candidate detection.

Rules only *nominate* facts about a sentence. They never make the final call on
temporal signals (state does) and the LLM may veto/refine them. Language only:
no emotion, lie or intent claims.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .text_utils import split_sentences

# (regex, confidence)
UNCERTAINTY = [
    (r"\bnot (?:really |entirely |completely )?(?:sure|certain|confident)\b", 0.9),
    (r"\bi guess\b", 0.85),
    (r"\b(?:maybe|perhaps)\b", 0.8),
    (r"\bprobably\b", 0.75),
    (r"\bi (?:don't|do not) know\b", 0.8),
    (r"\bno idea\b", 0.8),
    (r"\bhopefully\b", 0.7),
    (r"\bshould be (?:okay|ok|fine|alright)\b", 0.7),
    (r"\b(?:kind of|sort of)\b", 0.6),
    (r"\bi think\b", 0.55),
    (r"\bmight\b", 0.55),
    (r"\bcould\b", 0.5),
]

HEDGING = [
    (r"\bi suppose\b", 0.8),
    (r"\bshould probably\b", 0.8),
    (r"\bcould (?:potentially|possibly)\b", 0.8),
    (r"\bthat (?:could|might|should probably) (?:work|be fine|be okay|be ok)\b", 0.8),
    (r"\bi guess (?:that's|that is|it's|it is|we could|that could|that works)\b", 0.85),
    (r"\bif we have to\b", 0.7),
    (r"\b(?:okay|fine) with (?:it|that),? (?:i guess|i suppose)\b", 0.85),
]

COMMITMENT = [
    r"\bi(?:'ll| will)\s+(?!not\b|be right back\b|see\b)(?P<a>.+)",
    r"\bi(?:'m| am) going to\s+(?!not\b)(?P<a>.+)",
    r"\bi can (?P<a>(?:handle|take|do|finish|prepare|own|get|send|write|build|fix|deploy)\b.*)",
    r"\blet me (?P<a>(?:handle|take|do|finish|get|check|prepare)\b.*)",
    r"\bi(?:'ve| have) got (?P<a>(?:it|this)\b.*)",
]

WEAKEN = [
    r"\bi (?:don't|do not) think i(?:'ll| will)\b",
    r"\bi (?:won't|will not|can't|cannot|can not) (?:be able|make it|finish|do|handle|get)\b",
    r"\bi(?:'m| am) (?:not going to|not gonna|unable to|not able to)\b",
    r"\b(?:not going to|don't|do not|won't) (?:have|get) (?:enough )?time\b",
    r"\bnot going to be able\b",
    r"\bi (?:might|may|probably) not\b",
    r"\bi (?:probably )?won't\b",
    r"\bneed to (?:push|delay|postpone)\b",
    r"\bi(?:'m| am) (?:swamped|overloaded|too busy)\b",
]

CONCERN = [
    r"\b(?:worried|concerned|nervous|uneasy)\b",
    r"\b(?:biggest|main|my|a|the) (?:concern|worry|risk)\b",
    r"\bconcern\b",
    r"\bcould cause\b",
    r"\b(?:we're|we are|not) (?:not )?ready\b",
    r"\bnot comfortable\b",
    r"\brisky\b",
]

POSITION = [
    r"\b(?:we|you) should (?:use|go with|pick|choose)\b",
    r"\bi (?:still )?prefer\b",
    r"\bmakes more sense\b",
    r"\blet's (?:use|go with)\b",
    r"\bi(?:'d| would) (?:rather|go with|use)\b",
]

EXPLICIT_DISAGREE = [
    r"\bi (?:disagree|don't agree|do not agree)\b",
    r"\bnot convinced\b",
    r"\bi don't think (?:that's|that is|that works|we should)\b",
]

DECISION = [
    r"\b(?:let's|we'll|we will) go with\b",
    r"\bagreed\b",
    r"\b(?:we've|we have) decided\b",
    r"\bthe decision is\b",
    r"\bfinal decision\b",
    r"\bwe're going with\b",
]

WH_START = re.compile(r"^(?:who|what|when|where|why|how|which|can|could|should|would|do|does|did|is|are|will)\b", re.I)


@dataclass
class Fact:
    kind: str  # uncertainty|hedging|commitment|weaken|question|concern|position|disagree|decision
    sentence: str
    confidence: float = 0.8
    extra: dict = field(default_factory=dict)


def _first(patterns, s):
    for p in patterns:
        m = re.search(p, s, re.I)
        if m:
            return m
    return None


def _score(patterns, s) -> float:
    hits = [c for p, c in patterns if re.search(p, s, re.I)]
    if not hits:
        return 0.0
    return min(0.95, max(hits) + 0.08 * (len(hits) - 1))


def _clean_action(a: str) -> str:
    a = re.split(r"[.!?;]| but | and then ", a, maxsplit=1)[0].strip(" ,")
    return a[:1].upper() + a[1:] if a else a


def _options(sentence: str) -> list[str]:
    opts = re.findall(r"\b(?:use|prefer|with|choose|pick)\s+([A-Za-z][\w+#.-]*)", sentence)
    m = re.search(r"([A-Za-z][\w+#.-]*)\s+makes more sense", sentence)
    if m:
        opts.append(m.group(1))
    stop = {"the", "a", "an", "it", "that", "this", "to", "in", "on"}
    return [o for o in opts if o.lower() not in stop]


def analyze(text: str) -> list[Fact]:
    facts: list[Fact] = []
    for s in split_sentences(text):
        weak = _first(WEAKEN, s)
        if weak:
            facts.append(Fact("weaken", s, 0.85))

        if not weak:
            for p in COMMITMENT:
                m = re.search(p, s, re.I)
                if m:
                    facts.append(Fact("commitment", s, 0.85, {"action": _clean_action(m.group("a"))}))
                    break

        hedge = _score(HEDGING, s)
        if hedge and not weak:
            facts.append(Fact("hedging", s, hedge))
        elif not weak:
            unc = _score(UNCERTAINTY, s)
            if unc:
                facts.append(Fact("uncertainty", s, unc))

        if s.endswith("?") or (WH_START.match(s) and len(s.split()) >= 4 and "?" in s):
            facts.append(Fact("question", s, 0.8))

        if _first(CONCERN, s):
            facts.append(Fact("concern", s, 0.75))

        if _first(POSITION, s):
            facts.append(Fact("position", s, 0.75, {"options": _options(s)}))

        if _first(EXPLICIT_DISAGREE, s):
            facts.append(Fact("disagree", s, 0.75))

        if _first(DECISION, s):
            facts.append(Fact("decision", s, 0.8))
    return facts
