# WiseMouth — Detailed Implementation Plan

Derived from `WiseMouth_48_Hour_Hackathon_Plan (1).md`. That doc is the product spec; this is the build order, with concrete contracts, files, and "done" checks per phase.

## 0. Decisions to lock before coding

| Question | Decision | Why |
|---|---|---|
| Who is the "speaker"? | **One browser tab = one participant.** Each tab joins a room with a name and streams its own mic. Speaker = the name on that WebSocket. | Avoids diarization on a shared mic (unreliable). Multi-speaker demo works with 2–3 tabs/laptops. |
| Solo fallback | A "speaker selector" dropdown in a single tab, so one presenter can voice Sarah/John/Maria. | Demo works with one person and one mic. |
| Audio path | Browser → FastAPI WS (PCM16, 16 kHz mono) → AssemblyAI streaming WS. FastAPI is the single place that produces transcript events. | Keeps API key server-side; demo mode can inject text into the same pipeline. |
| Demo Mode B | Scripted lines are pushed into the **same** `ingest_utterance()` function that AssemblyAI finals use. | Spec requires the fallback to use the real engine, not fake output. |
| LLM | Groq primary → Gemini fallback, behind one `LLMClient` interface with JSON-schema output and a 4s timeout. | Spec. Failover must be automatic and silent. |
| DB | Postgres via Docker; SQLAlchemy. **In-memory state is source of truth during a session; DB is written async.** | A DB hiccup must never stall the live UI. |
| Auth | None. Room code + display name. | Spec: out of scope. |
| Vocabulary | Signal labels are observable-language only ("Uncertainty language detected"). Never emotion/lie wording. | Product boundary (spec §7). Enforce in prompts and UI copy. |

Verify the AssemblyAI streaming API version/endpoint and auth method (temp token vs. API key header) against current docs at the start of Phase 2 — don't rely on memory.

## 1. Repository layout

```
wisemouth/
  frontend/                 Next.js (App Router) + TS + Tailwind + shadcn
    app/
      page.tsx              Landing
      meeting/[room]/page.tsx   Live meeting + radar
      report/[id]/page.tsx  Report + timeline
    components/{meeting,radar,transcript,timeline,ui}/
    hooks/{useMic,useMeetingSocket}.ts
    lib/{types.ts,api.ts,audio-worklet.js}
  backend/app/
    main.py
    api/{ws_meeting.py,routes.py}
    services/{assemblyai.py,llm.py,rules.py,signal_engine.py,conversation_state.py,demo_script.py}
    models/   SQLAlchemy tables
    schemas/  Pydantic (Signal, TranscriptEvent, WS events)
  tests/                    pytest: rules, state, engine w/ fake LLM
  docker-compose.yml  .env.example  README.md
```

## 2. Core contracts (define first, in Phase 0)

**Pydantic `Utterance`**: `id, room, speaker, text, start_ms, is_final`.

**`Signal`**: `id, type, speaker, evidence, timestamp_ms, confidence, topic, related: {text, timestamp_ms} | None, meta`.
`type` enum: `uncertainty | hedging | commitment | commitment_change | repeated_concern | disagreement | unanswered_question`.

**WS events server→client**: `transcript_partial`, `transcript_final`, `signal`, `signal_update` (e.g., question later answered), `state_snapshot` (on join/reconnect), `error`, `session_ended`.
**Client→server**: binary audio frames, `{"type":"join","name":..}`, `{"type":"mute"}`, `{"type":"end"}`, `{"type":"demo_start"}`.

Mirror these types in `frontend/lib/types.ts`. Any change to the contract is edited in both places in the same commit.

## 3. Phases

### Phase 0 — Foundation (target ~3h)
- Monorepo, `.gitignore` (incl. `.env`), `.env.example` (never commit keys).
- `docker-compose.yml` with Postgres; backend `uvicorn`; frontend `next dev`.
- FastAPI `/health` and `/ws/meeting/{room}` that echoes a hello; Next page that connects and shows "connected".
- SQLAlchemy models for the 5 tables; `create_all` on startup (no Alembic — hackathon).
- **Done when:** one command starts everything; browser shows live WS round-trip.

### Phase 1 — Live transcription (target ~6h) — **gate: do not proceed until reliable**
- `lib/audio-worklet.js`: AudioWorklet downsampling mic to 16 kHz PCM16 in ~50–100 ms frames.
- `useMic` hook: permission handling, mute/unmute, device error states.
- `services/assemblyai.py`: async client with one AssemblyAI session per participant; forwards frames, emits partial/final `Utterance`s; auto-reconnect with backoff; keep-alive.
- Broadcast transcript events to everyone in the room; per-room in-memory registry of participants.
- Persist finals to `transcript_segments` (fire-and-forget task).
- Transcript panel: speaker, timestamp, live-recording dot, partial text greyed until final.
- **Done when:** 10-minute continuous session with two tabs, no dropped connection, latency to final text feels < ~1.5s; mute works; killing/restoring network recovers.

### Phase 2 — Signal engine v1 (target ~6h)
- `rules.py`: regex/lexicon candidate detector returning `{categories: [...], matched_spans}` per utterance. Lexicons from spec §11, plus negation/weakening phrases for commitment change ("don't think I'll", "won't be able", "not going to have time", "actually"). Pure functions, unit-tested.
- `llm.py`: `LLMClient.extract(utterance, context) -> list[Signal]` using JSON mode + Pydantic validation; one retry on invalid JSON; provider failover; timeout; returns `[]` (and logs) on total failure rather than raising.
- Prompt rules: only observable language; quote evidence verbatim from the utterance; output a confidence; no emotion/lie inference; allowed types only. Include the last ~6 utterances as context.
- `signal_engine.ingest_utterance(u)`: rules → (if candidate) LLM → validate evidence is a substring of the text (drop hallucinated evidence) → hand to state → emit events. Run per-utterance as background tasks so transcript is never blocked; keep order via per-room queue.
- Uncertainty/hedging get a **rules-only fast path** (emit immediately, LLM refines confidence/label if it returns) so the radar reacts instantly even if the LLM is slow.
- **Done when:** unit tests pass on a fixture of ~30 labelled sentences; running the demo script produces uncertainty, hedging, and commitment signals with evidence.

### Phase 3 — Live radar UI (target ~6h)
- Meeting layout (spec "Recommended Demo Layout"): participant tiles, mic/camera/leave controls, transcript, radar.
- `RadarPanel`: 7 counters with count-up animation, coloured per type, driven by a reducer over `signal` events (idempotent on `signal.id` so reconnect snapshots don't double count).
- `LiveSignalCard`: latest signal with evidence and, for changes, Earlier/Now side by side. Signal chips inline in transcript lines; click opens `SignalDetail` drawer (type, speaker, evidence, timestamp, related statement, confidence, topic).
- Camera preview local only (no WebRTC). Participant tile shows speaking indicator from utterance activity.
- **Done when:** speaking into the mic makes counters and the live card update with no reload.

### Phase 4 — Temporal intelligence (target ~6h)
`conversation_state.py` per room holds commitments, questions, concerns, disagreements, topics, signals.

- **Commitments:** on `commitment`, store `{speaker, action, topic, ts, status=active}`.
- **Commitment change:** for an utterance from a speaker with active commitments and a weakening candidate from rules → ask LLM one focused question: "Does this statement retract/weaken commitment X? yes/no + reason". If yes: emit `commitment_change` with `related` = original, mark commitment `changed`. Only same-speaker comparisons.
- **Unanswered questions:** on a question candidate, record it with an answer window (e.g., next 3 utterances from a different speaker or ~45s). On expiry with no plausible answer (cheap LLM yes/no on the following utterances, or heuristic: no other-speaker utterance) → emit `unanswered_question`. If answered later, emit `signal_update` to clear it.
- **Repeated concern:** on concern candidate, LLM assigns a canonical topic label matched against existing concern topics (pass existing labels in the prompt so it reuses them). Emit `repeated_concern` on the 2nd mention, update count on the 3rd; keep evidence list.
- **Disagreement:** LLM flags opposition between two speakers on the same topic; emit when the position is restated with no decision; add a "decision" detector (phrases like "let's go with", "agreed") that resolves it.
- Sweep task runs every few seconds for expiring windows; on `end` it flushes pending items.
- **Done when:** the spec §21 demo script (commitment → uncertainty → repeated concern → commitment change → unanswered question) yields exactly the expected signals in tests using a **recorded LLM fixture** plus once against the live LLM.

### Phase 5 — Report and timeline (target ~5h)
- `POST end` → status `ended`, final flush, persist signals/commitments/questions.
- `GET /api/conversations`, `GET /api/conversations/{id}` (segments + signals).
- Report page: totals per type (matches spec §21 layout), Recharts bar/summary, chronological timeline with clickable evidence, transcript with highlighted evidence spans, conversation history list.
- **Done when:** ending a demo run lands on a report identical to what the radar showed.

### Phase 6 — Demo mode and resilience (target ~5h)
- `demo_script.py`: the spec's scripted conversation with timings; "Start Demo" button feeds lines through `ingest_utterance` at realistic pace, with distinct speaker names and typed-out partials so it looks live.
- **LLM response cache** keyed on (utterance text, context hash) so the rehearsed script replays deterministically and survives an LLM outage. Ship a pre-warmed cache for the demo script.
- Failure handling in UI: mic denied, AssemblyAI disconnect (banner + one-click "switch to demo mode"), backend disconnect (auto-reconnect + `state_snapshot`), LLM down (rules-only badge).
- Empty/loading states, responsive layout, animations.
- Optional: Ollama provider behind the same interface.

### Phase 7 — Deploy, rehearse, pitch (target ~6h)
- Deploy backend (Render/Oracle) and frontend (Vercel); check WS works over `wss` and that the host doesn't sleep (Render free cold start: ping before demo).
- Full rehearsal on the *demo* network and hardware; record a backup video of a good run.
- Feature freeze at hour 44. Slides: problem, live demo, architecture, boundaries slide ("observable language, not emotions"), roadmap.

## 4. Testing strategy (feedback loops)
- **Unit:** rules lexicon, evidence-substring validation, state transitions (commitment change, question expiry, concern counting), Pydantic schema round-trips.
- **Engine integration:** `FakeLLM` returning canned JSON → assert emitted event sequence for the full demo script.
- **Live smoke script:** `scripts/smoke.py` opens the WS, plays the demo script, and asserts signal counts. Run before every deploy.
- **UI:** Playwright headless: start demo mode, assert counters reach expected values, screenshot the meeting and report pages for a visual check.
- **Audio:** manual 10-minute soak test in Phase 1, plus a pre-recorded WAV streamed through the pipeline as a repeatable test.

## 5. Risk register

| Risk | Mitigation |
|---|---|
| Mic/AssemblyAI flaky at venue | Demo Mode B through the real engine; backup video |
| LLM latency/rate limit | Rules fast path, provider failover, cache, timeouts |
| Hallucinated evidence | Substring check against source text; drop if it fails |
| Speaker attribution wrong | One participant per tab; explicit speaker selector solo |
| False positives ("could" everywhere) | Rules only nominate; LLM decides; confidence threshold (~0.6) on display |
| Free tier cold starts / sleep | Keep-alive ping; local backend as backup |
| Scope creep into video conferencing | Enforce spec §"48-Hour Scope Rule": no WebRTC, chat, or scheduling |
| Secrets leaking into repo or logs | `.env` ignored; never log keys or full audio; scan before each push |
| Privacy of real conversations | Demo with staged/consented speech only; note in README |

## 6. Priority cuts (if behind schedule, cut from the bottom)
1. Meeting visual polish, camera preview
2. Conversation history page
3. Disagreement detection
4. Repeated-concern count updates (keep basic 2nd-mention alert)
5. Recharts (use plain counters)

**Never cut:** mic → transcript, commitment + commitment change, unanswered question, evidence display, demo mode.

## 7. Suggested first session
1. Phase 0 scaffold and contracts, commit.
2. Get a WAV file streaming through AssemblyAI to a printed transcript (proves the hardest external dependency early).
3. Build `rules.py` + tests while that runs; these are cheap and unblock everything.
