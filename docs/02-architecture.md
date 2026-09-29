# 02 Architecture

```
Browser tab (one per participant)
  mic -> AudioWorklet (16 kHz PCM16, 100 ms frames)
        |  WebSocket  /ws/meeting/{room}   (binary audio + JSON control)
        v
FastAPI gateway (ws_meeting.py)  ── Room (room.py) ── broadcasts events to every tab
        |                                   |
        |  per-participant                  v
        v                            SignalEngine (signal_engine.py)
AssemblyAI streaming STT                    |
  partial / final turns  ─────────►  rules.analyze()  ──►  LLM refine (optional)
                                            |
Typed line ("say") ─────────────────────────┤        ConversationState.process()
Demo script  ───────────────────────────────┘           (temporal intelligence)
                                                            |
                                          signal / signal_update events ──► UI radar
                                                            |
                                                   SQLAlchemy -> Postgres (async, best-effort)
```

**Key invariant:** live speech, typed text and the demo script all enter through `Room.final()` -> `SignalEngine.ingest_utterance()`. The demo is therefore *real engine output*, not a pre-rendered result.

## Backend module map (`backend/app`)

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app, lifespan (DB init, LLM client, room manager), CORS |
| `config.py` | Settings from env / `.env` (pydantic-settings) |
| `api/ws_meeting.py` | WebSocket gateway: join, audio frames, mute, say, demo_start, end |
| `api/routes.py` | `/health`, `/api/config`, `/api/conversations[/{id}]` |
| `services/room.py` | `Room` (participants, transcript, broadcast, lifecycle) and `RoomManager` |
| `services/assemblyai.py` | One AssemblyAI v3 streaming session per participant, auto-reconnect |
| `services/rules.py` | Regex/lexicon candidate detection -> `Fact`s |
| `services/llm.py` | Groq -> Gemini client, JSON mode, timeout, on-disk cache, `refine/weakens/answers` |
| `services/conversation_state.py` | Commitments, questions, concerns, positions, disagreements; emits events |
| `services/signal_engine.py` | Orchestrates rules -> LLM -> state, serialised per room |
| `services/demo_script.py` | Deterministic demo conversation (Mode B) |
| `services/text_utils.py` | Sentence split, content tokens, fuzzy token match, timestamps |
| `models/db.py` | SQLAlchemy tables + fire-and-forget persistence helpers |
| `schemas/events.py` | Pydantic `Signal`, `Utterance`, `SignalType` (mirrored in `frontend/lib/types.ts`) |

## Data flow for one utterance

1. STT final (or typed/demo text) -> `Room.final(speaker, text)`: timestamps it (ms since room start), stores + broadcasts `transcript_final`, persists the segment, and **schedules analysis as a background task** so the transcript is never blocked by analysis.
2. `SignalEngine.ingest_utterance` (per-room lock -> ordered): `rules.analyze(text)` returns `Fact`s per sentence.
3. If an LLM is configured and any fact is ambiguous, `LLMClient.refine` may drop a fact, relabel uncertainty<->hedging, extract a commitment's action, or adjust confidence. High-confidence lexical hits (>= 0.8) skip the LLM entirely. Any LLM failure -> facts pass through unchanged.
4. `ConversationState.process` turns facts into `Signal`s, connecting them to history (commitment -> change, question -> unanswered, concern -> repeated, positions -> disagreement, decision -> resolves).
5. Events (`signal` / `signal_update`) broadcast to all tabs with fresh counts, and persisted.
6. A 3 s sweeper flags questions unanswered after 25 s; `end` flushes anything still pending.

## Safety nets

- **Evidence integrity:** evidence is always the source sentence from the transcript (the LLM can only keep/drop/refine, never write evidence).
- **LLM is optional and bounded:** 3.5 s timeout, provider failover (Groq -> Gemini), response cache (`backend/data/llm_cache.json`) so repeated demo runs are instant and deterministic.
- **Persistence is best-effort:** in-memory state is the source of truth while live; DB writes run in threads and swallow errors.
- **Reconnect:** the client reconnects with backoff and receives a full `state_snapshot`; reducers are idempotent on signal/segment ids.

## Storage

Tables: `conversations`, `transcript_segments`, `signals` (full signal JSON in `signal_metadata`), `commitments`, `questions`. Created on startup (`create_all`, no migrations). `DATABASE_URL` empty -> SQLite at `backend/data/wisemouth.db`; docker-compose uses Postgres 16.
