# 11 Status and roadmap

Last updated: 2026-09-29.

## Built and verified

| Area | Status | Evidence |
|---|---|---|
| Backend (FastAPI, WS gateway, rooms, persistence) | Done | 31 pytest tests pass; runs in Docker with Postgres |
| Signal engine: rules + LLM refine + temporal state | Done | Demo script yields exact expected counts (unit + smoke) |
| All 7 signal types with evidence | Done | `test_engine.py`, report screenshots |
| AssemblyAI streaming relay | Implemented; **tested against a fake server only** | `test_assemblyai.py`. Not yet run with a real key/mic |
| LLM client (Groq -> Gemini, cache, timeouts, circuit breaker, startup model check) | Implemented; resilience covered with mocked HTTP; **live keys not yet confirmed working** | `test_llm.py`. First real run 404'd on stale default models, which prompted the breaker + model discovery |
| Frontend: landing, meeting, radar, drawer, report, history | Done | `tsc` + `next build` clean; Playwright screenshots in `docs/assets` |
| Demo mode through the real engine | Done | `scripts/smoke.py` OK; Playwright run |
| Docker compose (Postgres + backend + frontend) | Done | Brought up and used for the checks above |

## Not done / to verify next (in priority order)

1. **Real-mic test** with an AssemblyAI key: two tabs, 10-minute soak, latency. Confirm the v3 streaming parameters against current docs.
2. **LLM run** with Groq/Gemini keys: check refine output quality, warm `llm_cache.json`.
3. Deploy (Vercel + Render/Oracle) and run `scripts/smoke.py` against it.
4. Mobile/narrow layout pass (works via Tailwind grid but unreviewed).
5. Automated Playwright test committed to the repo.
6. Rehearsal and backup recording.

## Roadmap ideas (post-hackathon)

- Provider adapters (Meet/Zoom/Teams bots) feeding `Room.final()`.
- Real diarization for single-mic rooms.
- Persisted commitment/question tracking dashboards across meetings.
- Multi-language lexicons; per-team lexicon tuning; evaluation set with labelled transcripts.
- Auth, room access control, retention/redaction controls for sensitive (e.g. health) conversations.
- Alembic migrations; horizontal scale via shared state (Redis) once needed.

## Change log

- 2026-09-29 - Initial full build: backend, frontend, docs, tests, compose.
