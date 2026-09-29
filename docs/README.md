# WiseMouth Documentation

Start here. Everything needed to run, demo, extend and deploy WiseMouth.

| Doc | Read it when you want to... |
|---|---|
| [01 Product overview](01-product-overview.md) | Understand what WiseMouth is, what it will and won't claim, and the pitch |
| [02 Architecture](02-architecture.md) | See how audio becomes signals; module map; data flow |
| [03 Getting started](03-getting-started.md) | Run it locally (Docker or native), set API keys |
| [04 Signal catalog](04-signal-catalog.md) | Know exactly how each signal is detected and its limits |
| [05 API and events](05-api-and-events.md) | Integrate with the WebSocket / REST contract |
| [06 Frontend guide](06-frontend-guide.md) | Change the UI: pages, components, hooks, styling |
| [07 Demo runbook](07-demo-runbook.md) | Present it: setup checklist, script, fallbacks, pitch |
| [08 Testing](08-testing.md) | Run unit, smoke and browser tests |
| [09 Deployment](09-deployment.md) | Ship to Vercel + Render/Oracle with Postgres |
| [10 Decisions and troubleshooting](10-decisions-and-troubleshooting.md) | Why things are the way they are; fixing common problems |
| [11 Status and roadmap](11-status-and-roadmap.md) | What's built, what's verified, what's next |
| [00 Hackathon spec](00-hackathon-spec.md) | The original product spec (source of truth for intent) |
| [12 Implementation plan](12-implementation-plan.md) | The original phased build plan |

Screenshots: [meeting](assets/meeting.png), [evidence drawer](assets/evidence-drawer.png), [report](assets/report.png).

## 60-second quick start

```bash
cp .env.example .env        # optional: add ASSEMBLYAI_API_KEY (and GROQ_API_KEY) for mic + LLM
docker compose up --build
# open http://localhost:3000  -> Start Conversation -> "Run demo conversation"
```

No keys are required: typed input and the demo conversation run through the full engine with rules-only analysis.
