# 03 Getting started

## Prerequisites

- **Docker Desktop** (easiest; runs Postgres + backend + frontend), or
- Node 20+ and Python 3.12+ for native development.
- A Chromium-based browser (Chrome/Edge) for the mic.

## Configure

```bash
cp .env.example .env
```

| Variable | Needed for | Notes |
|---|---|---|
| `ASSEMBLYAI_API_KEY` | Microphone / live transcription | Without it the mic button is disabled; typed input and demo still work |
| `LLM_PROVIDER` | LLM refinement | `groq` (default) / `gemini` / `none` |
| `GROQ_API_KEY`, `GEMINI_API_KEY` | LLM refinement | The non-primary provider is the automatic fallback if its key is set |
| `DATABASE_URL` | Persistence | Empty -> SQLite. Compose injects Postgres. Accepts `postgresql://` URLs |
| `NEXT_PUBLIC_API_URL` | Frontend -> backend | Default `http://localhost:8000` |

Never commit `.env` (it is git-ignored). Keys stay server-side; the browser only talks to your backend.

## Run with Docker (recommended)

```bash
docker compose up --build
```

- App: http://localhost:3000
- API: http://localhost:8000 (`/health`, `/api/config`)
- Code changes in `backend/app` and `frontend/{app,components,hooks,lib}` hot-reload.

Check what's enabled: `curl localhost:8000/api/config` -> `{"stt": true|false, "llm": "groq+gemini"|"rules-only"}`.

## Run natively

```bash
# backend
cd backend
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend (new terminal)
cd frontend
npm install
npm run dev
```

## First run

1. Open http://localhost:3000, enter a name, click **Start Conversation**.
2. Click **Run demo conversation** - watch transcript, chips and radar fill in (~45 s).
3. Click **End & view report**.
4. With an AssemblyAI key: click **Start mic** and speak, e.g. "I'll handle the deployment." then later "Actually, I don't think I'll have enough time to handle the deployment."
5. Multi-speaker: share the room code (top-left chip) and open the URL from a second tab/device with a different name. Each tab streams its own mic; speaker = tab name.
6. Solo presenter: use the "speaking as" box + text input to voice other participants.

## Secrets hygiene

Keep API keys only in `.env` / your host's secret store. Do not paste them into chat, issues or commits. If a key leaks, rotate it.
