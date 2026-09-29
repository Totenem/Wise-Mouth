# 10 Decisions and troubleshooting

## Design decisions (and why)

| Decision | Why |
|---|---|
| One browser tab = one participant; speaker = name | Diarization on a shared mic is unreliable; this makes multi-speaker demos deterministic |
| Audio goes browser -> FastAPI -> AssemblyAI | Keeps the API key server-side; lets typed/demo input share one pipeline |
| Demo mode uses the real engine | Spec requirement: the fallback must not be a fake pre-rendered result |
| Rules nominate, LLM only refines | Lower cost/latency, deterministic behaviour, and the LLM cannot invent evidence |
| Evidence = source sentence | Transparency; nothing to hallucinate |
| Deviation from spec: no separate "instant rules fast path then LLM update" | Instead: high-confidence lexical hits skip the LLM entirely, and LLM calls have a 3.5 s timeout and cache. Simpler, same effect on latency |
| In-memory room state; async DB writes | A DB hiccup must never freeze the live UI. Single backend instance |
| `create_all`, no Alembic | Hackathon scope; add migrations before real users |
| SQLite fallback when `DATABASE_URL` is empty | Runs anywhere with zero setup; compose uses Postgres |
| Tests run without an LLM | Deterministic CI; LLM behaviour is layered on top |

## Troubleshooting

| Problem | Cause / fix |
|---|---|
| Start mic button disabled | `ASSEMBLYAI_API_KEY` not set on the backend (`curl :8000/api/config`) |
| "Connection lost. Reconnecting..." | Backend down/unreachable or wrong `NEXT_PUBLIC_API_URL`. Check `docker compose logs backend` |
| Mic works but no transcript | Check backend log for `AssemblyAI connection lost`; verify key/quota; the AssemblyAI v3 URL/params may have changed - see [05](05-api-and-events.md) |
| Signals show `rules-only` | No `GROQ_API_KEY`/`GEMINI_API_KEY` (fine) or `LLM_PROVIDER=none` |
| No commitment change fired | Same speaker must have made the earlier commitment, and the weakening sentence should share a topic word (e.g. "deployment"), or there must be exactly one active commitment |
| Chips/dots uncoloured | Tailwind isn't scanning a directory holding class names; see [06](06-frontend-guide.md) |
| Demo button disabled | Not connected yet (button waits for the WebSocket) |
| Docker on Windows: `working directory ... is invalid` from Git Bash | Prefix with `MSYS_NO_PATHCONV=1` and use `$(pwd -W)` for volume paths |
| Port 5432/8000/3000 in use | Stop the other process or change the published ports in `docker-compose.yml` |
| Log shows `LLM groq disabled ... HTTP 404` | Configured model doesn't exist for your key. Startup now checks the provider model list and switches to a valid model automatically (see `curl :8000/api/config` -> `llm_status`); a provider that still fails is disabled (1 h for 400/401/403/404, 30 s for 429, 10 s for 5xx/timeouts) instead of being retried on every utterance. Override with `GROQ_MODEL` / `GEMINI_MODEL` |
| LLM answers stale after prompt change | Delete `backend/data/llm_cache.json` (cache is keyed by the exact prompt) |

## Known limitations

See [04](04-signal-catalog.md#known-limits). Also: no auth (anyone with a room code can join), room state lost on backend restart while live, no diarization, English only.
