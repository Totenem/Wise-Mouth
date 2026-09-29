# 08 Testing

## Backend unit + integration (pytest)

```bash
cd backend && pip install -r requirements.txt && python -m pytest -q
# or, with only Docker installed (Git Bash on Windows needs MSYS_NO_PATHCONV=1):
docker run --rm -v "$PWD:/app" -w /app python:3.12-slim sh -c "pip install -q -r requirements.txt && python -m pytest -q"
```

| File | Covers |
|---|---|
| `tests/test_rules.py` | Lexicon detection per signal kind, weakened-sentence-not-commitment, weak markers below threshold, action extraction |
| `tests/test_engine.py` | Full demo script -> exact signal counts; commitment change evidence/timestamps; other-speaker isolation; repeated concern count/update events; answered vs unanswered questions; late answer resolution; decision resolves disagreement; same option = agreement |
| `tests/test_assemblyai.py` | Session against a local fake streaming server: auth header, audio relay, partial vs final (formatted) turns |
| `tests/test_llm.py` | Circuit breaker (404 -> one attempt per provider, then disabled), provider failover, startup model discovery/replacement, bad-key disable |
| `tests/test_ws.py` | Real FastAPI app: join -> typed line -> transcript + signal events -> end -> `session_ended` -> REST report |

The engine tests run with **no LLM** (deterministic). Status at last run: **31 passed**.

## End-to-end smoke (running stack)

```bash
python scripts/smoke.py http://localhost:8000     # needs: pip install websockets
```

Plays the demo over the real WebSocket at 10x speed, ends the session and asserts the expected signal counts. Prints `OK` on success. Run before every deploy and demo. (Verified against the docker-compose stack with Postgres.)

## Browser check (Playwright)

Not committed as a suite; the verification used Playwright (Python) in Docker to: open landing, join a room, click *Run demo conversation*, screenshot, open the *Commitment changed* drawer, end the call, and screenshot the report. Screenshots are in `docs/assets/`. To repeat, run `mcr.microsoft.com/playwright/python` with `--host-resolver-rules="MAP localhost host.docker.internal"` so the browser inside the container reaches the host's `localhost:3000/8000`.

## Manual checks that need real hardware/keys

- [ ] 10-minute two-tab mic soak with AssemblyAI (no disconnects; partials -> finals < ~1.5 s)
- [ ] Kill network mid-session -> banner -> reconnect -> transcript intact
- [ ] Demo script once with Groq/Gemini keys (cache warm-up; verify labels match rules-only run)
- [ ] Mic permission denied path shows the error
- [ ] Mobile/narrow viewport sanity check

## Frontend static checks

```bash
cd frontend && npx tsc --noEmit && npx next build
```
