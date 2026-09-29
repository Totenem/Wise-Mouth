# 09 Deployment

Target: frontend on Vercel, backend on Render or Oracle Cloud, Postgres from a free tier. Pick whichever is more reliable on the day. **Not yet deployed** - this is the recipe.

## Backend (Render web service)

- Root directory: `backend`, runtime Docker (uses `backend/Dockerfile`) or Python with `pip install -r requirements.txt`.
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Env: `ASSEMBLYAI_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `LLM_PROVIDER`, `DATABASE_URL` (Render/Neon/Supabase Postgres URL - `postgres://` and `postgresql://` are auto-converted), `CORS_ORIGINS` (your Vercel URL, comma-separated; default `*`).
- WebSockets work on Render; the free tier **sleeps** - hit `/health` before the demo and consider a keep-alive ping.
- Single instance only: room state is in memory (by design for the MVP). Do not scale horizontally.

## Backend (Oracle Cloud VM alternative)

`docker compose up -d --build` on an always-free VM; put Caddy/nginx in front for TLS (browsers require `wss://` from an https page and secure context for the mic).

## Frontend (Vercel)

- Root directory: `frontend`, framework Next.js.
- Env: `NEXT_PUBLIC_API_URL=https://<backend-host>` (build-time). The WebSocket URL is derived (`https` -> `wss`).
- Microphone requires HTTPS (Vercel provides it) or `localhost`.

## Post-deploy verification

1. `curl https://<backend>/api/config` -> expected `stt`/`llm` flags.
2. `python scripts/smoke.py https://<backend>` -> `OK`.
3. Open the Vercel URL on the demo network, run the demo, then the mic.

## Secrets

Set keys only in the host's secret store. `.env` is git-ignored; `.env.example` contains no values. Rotate any key that was ever pasted into chat or logs.
