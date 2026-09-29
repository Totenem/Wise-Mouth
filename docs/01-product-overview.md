# 01 Product overview

**WiseMouth** - *See what the conversation doesn't explicitly say.*

A transcript tells you what people said. WiseMouth identifies the **observable signals that emerge across a conversation**: uncertainty, hedged agreement, commitments, changed commitments, repeated concerns, unresolved disagreements and unanswered questions. Every signal carries the evidence that produced it.

## Principles

1. **Observable language only.** No emotion detection, lie detection, personality profiling or claims about what someone "really" thinks. UI copy says *"uncertainty language detected"*, never *"Sarah is nervous"*.
2. **Evidence first.** Each signal has type, speaker, verbatim evidence, timestamp, confidence, topic and (for temporal signals) the earlier statement it relates to.
3. **Temporal intelligence is the differentiator.** Connecting "I'll handle the deployment" (00:01) to "I don't think I'll have enough time" (00:28) is the product.
4. **Hybrid engine.** Rules nominate candidates cheaply and deterministically; an LLM refines them; conversation state connects them over time.
5. **Degrades gracefully.** No mic key -> type or run the demo. No LLM key -> rules-only. DB down -> live UI unaffected.

## Signal types

| Signal | Meaning | Example |
|---|---|---|
| Uncertainty | Language signalling doubt | "I'm not sure we're ready for Friday." |
| Hedged agreement | Agrees/proposes with weakened commitment | "Yeah, I guess that could work." |
| Commitment | Explicit ownership of an action | "I'll handle the deployment." |
| Commitment changed | Same speaker later weakens/retracts it | "I don't think I'll have enough time." |
| Repeated concern | Same concern raised again | "...still my biggest concern." |
| Unresolved disagreement | Two speakers state competing positions, no decision | "Use PostgreSQL" vs "MongoDB makes more sense" |
| Unanswered question | Question with no response | "Who's going to handle the migration?" |

## Experience

- **Landing** - name + Start Conversation / Join by room code.
- **Meeting room** - participant tiles, live transcript with inline signal chips, mic/camera/demo/end controls, and the **Conversation Radar** (live counters + latest signal with earlier/now evidence).
- **Signal drawer** - click any chip/card for full evidence, confidence, topic, related statement.
- **Report** - totals, signal mix chart, chronological timeline, annotated transcript. Past conversations are listed under History.

The built-in meeting is a supporting environment, not a Google Meet competitor: one browser tab per participant, mic audio only, camera is a local preview.

## Out of scope (by design)

Zoom/Teams/Meet integrations, mobile app, browser extension, emotion/voice analysis, lie detection, profiling, model training, vector DB, Redis, Kafka, Kubernetes, auth, billing, multi-tenancy, screen share, chat, recording.

## Pitch

> "A transcript tells you what people said. WiseMouth identifies the signals that emerge across the conversation."
> ...John said he would handle deployment. Later, John said he probably won't have time. WiseMouth connects those two moments.
> "We're not just recording conversations. We're understanding how they evolve."

Positioning: **a real-time intelligence layer for online conversations** - independent of any conferencing provider.
