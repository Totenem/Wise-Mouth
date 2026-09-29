# 04 Signal catalog

How each signal is detected, what evidence it carries, and known limits. Source: `services/rules.py` (candidates) and `services/conversation_state.py` (logic). Rules operate **per sentence**. A signal is shown only if confidence >= `min_signal_confidence` (0.6).

## Per-utterance signals

### Uncertainty (`uncertainty`)
Lexicon with weights: "not sure/certain" .90, "I guess" .85, "maybe/perhaps" .80, "probably" .75, "I don't know/no idea" .80, "hopefully" .70, "should be okay" .70, "kind of/sort of" .60, "I think" .55, "might" .55, "could" .50. Multiple hits add +0.08 each. Weak markers alone ("I think", "could") stay below threshold, so ordinary opinions are not flagged; the LLM can raise them.
Suppressed when the sentence is a commitment-weakening statement.

### Hedged agreement (`hedging`)
Agreement/proposal with softened commitment: "I suppose", "should probably", "could potentially", "that could/might work", "I guess that's fine / we could", "if we have to". Takes precedence over uncertainty for the same sentence (no double count).

### Commitment (`commitment`)
"I'll / I will X", "I'm going to X", "I can (handle|take|do|finish|prepare|...)", "let me (handle|...)", "I've got it". Action = text after the trigger. Not a commitment if the same sentence weakens it. Stored as an active commitment for that speaker.

## Temporal signals

### Commitment changed (`commitment_change`)
Trigger: weakening language ("I don't think I'll", "I won't be able to", "not going to have time", "I might not", "need to push", ...).
Logic: same speaker only; pick the active commitment with the most content-word overlap (e.g. "deployment"). Overlap -> confidence 0.92. No overlap -> 0.70, and if an LLM is configured it is asked whether the statement weakens the commitment (veto on "no"). With several active commitments and no overlap/LLM it stays silent rather than guess.
Evidence: `related` = original commitment (text + timestamp), `evidence` = the weakening sentence, `meta.pattern` = "commitment -> weakened commitment".

### Repeated concern (`repeated_concern`)
Concern language ("worried", "concerned", "biggest concern", "could cause", "not ready", ...). Topic identity = content-word overlap with earlier concerns (fuzzy prefix match, so "migrate"/"migration" match). Signal appears on the **2nd** mention (`count=2`); further mentions update the same signal (`signal_update`, `count` grows) and keep all mentions in `meta.mentions`.

### Unresolved disagreement (`disagreement`)
Two forms: (a) a *position* ("we should use X", "I prefer X", "X makes more sense") from a different speaker within 8 utterances of another position, with a different option; (b) explicit "I disagree / not convinced". A *decision* phrase ("let's go with", "agreed", "we've decided") marks open disagreements `resolved` (`signal_update`) and they leave the radar count. Same option from both speakers = agreement.

### Unanswered question (`unanswered_question`)
Question = ends with "?" (or wh-start with "?"). A different speaker's next non-question utterance counts as an answer if it starts like an answer (yes/no/sure/"I can/I'll"), is a commitment, or shares a content word with the question (LLM asked as a last resort). After 2 non-answering utterances from others, or 25 s, or session end, the question is flagged. A late answer marks it `resolved`.

## Confidence

Rule confidence as above; LLM may override. UI shows High (>= .85), Medium (>= .70), Low.

## Known limits

- English only; lexicon-based, so novel phrasing is missed and sarcasm is invisible.
- "Answer" detection is heuristic; the LLM helps only when configured.
- Speaker identity is per browser tab (no diarization).
- Disagreement needs explicit position/objection phrasing.

## Adding or tuning a signal

1. Add patterns/weights in `rules.py` (+ a case in `tests/test_rules.py`).
2. Handle the new `Fact.kind` in `ConversationState.process`.
3. Add the type to `SignalType` (`schemas/events.py`), `lib/types.ts`, and `SIGNAL_META` in `lib/signals.ts`.
4. Add an engine test in `tests/test_engine.py`.
