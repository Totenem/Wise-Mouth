# 05 API and events

Base URL: `http://localhost:8000` (WebSocket: `ws://localhost:8000`). Types live in `backend/app/schemas/events.py` and `frontend/lib/types.ts` - keep them in sync.

## REST

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{"ok": true}` |
| GET | `/api/config` | `{"stt": bool, "llm": "groq+gemini" \| "groq" \| "gemini" \| "rules-only"}` |
| GET | `/api/conversations` | Latest 50: `[{id, title, started_at, status}]` |
| GET | `/api/conversations/{id}` | Live room: `{id, status, transcript, signals, counts}`. Ended: DB copy with `started_at`, `ended_at` |

## WebSocket `/ws/meeting/{room}`

Room = any string; created on first join. One connection per participant.

### Client -> server

1. First message (required): `{"type":"join","name":"John"}` (duplicate names get a numeric suffix).
2. **Binary frames**: PCM16 little-endian, 16 kHz, mono (~100 ms each). Ignored if the participant is muted or no STT key is configured.
3. JSON control:

| Message | Effect |
|---|---|
| `{"type":"mute"}` / `{"type":"unmute"}` | Stops/resumes forwarding audio; broadcasts participant list |
| `{"type":"say","speaker":"Sarah","text":"..."}` | Injects an utterance through the full pipeline (speaker optional) |
| `{"type":"demo_start","speed":1.0}` | Runs the deterministic demo conversation (speed multiplier) |
| `{"type":"end"}` | Flushes pending analysis, persists, broadcasts `session_ended` |

### Server -> client

| `type` | Payload |
|---|---|
| `state_snapshot` | Sent on join: `room, status, participants, transcript, signals, counts, capabilities{stt,llm}, you` |
| `participants` | `participants: [{name, muted}]` |
| `transcript_partial` | `speaker, text, start_ms` (interim; replace per speaker) |
| `transcript_final` | `id, speaker, text, start_ms` |
| `signal` | `signal: Signal, counts` - new signal |
| `signal_update` | `signal: Signal, counts` - same `id`, changed (count, status, evidence) |
| `error` | `message, source` (e.g. `stt` connection trouble) |
| `demo_finished` | Demo script completed |
| `session_ended` | Final snapshot (same shape as `state_snapshot`) |

### Signal

```json
{
  "id": "a1b2c3d4e5",
  "type": "commitment_change",
  "speaker": "John",
  "evidence": "Actually, I don't think I'll have enough time to handle the deployment.",
  "timestamp_ms": 28000,
  "confidence": 0.92,
  "summary": "John previously committed to handle the deployment; later language weakens that commitment.",
  "topic": "Handle the deployment",
  "related": {"speaker": "John", "text": "Okay, for the release, I'll handle the deployment.", "timestamp_ms": 1000},
  "status": "active",
  "count": 1,
  "participants": [],
  "meta": {"pattern": "commitment -> weakened commitment", "commitment_id": "..."}
}
```

`type` in: `uncertainty | hedging | commitment | commitment_change | repeated_concern | disagreement | unanswered_question`. `status` is `resolved` for answered questions / decided disagreements (excluded from radar counts). `timestamp_ms` is milliseconds since the room started.

### Client rules of thumb

- Treat `signal`/`signal_update` and transcript events as **idempotent by id** (reconnect sends a full snapshot).
- Recompute radar counts from the signal map (`countSignals`) rather than trusting incremental deltas.
- Reconnect with backoff; do not reconnect after `status == "ended"`.

## AssemblyAI (outbound)

`wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&encoding=pcm_s16le&format_turns=true`, header `Authorization: <key>`. `Turn` messages: interim while `end_of_turn=false`; final on `end_of_turn=true` **and** `turn_is_formatted=true`. Re-verify against AssemblyAI's current docs if behaviour changes; the URL is overridable via `ASSEMBLYAI_WS_URL`.
