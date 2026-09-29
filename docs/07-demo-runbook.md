# 07 Demo runbook

## T-24h checklist

- [ ] `docker compose up --build` works from a clean clone on the demo laptop
- [ ] `.env` has `ASSEMBLYAI_API_KEY`, `GROQ_API_KEY` (+ `GEMINI_API_KEY` fallback); `curl localhost:8000/api/config` shows `stt: true`
- [ ] Mic permission granted in the demo browser; chosen input device verified (level meter moves on the tile)
- [ ] Run the demo conversation once **with the LLM on** so `backend/data/llm_cache.json` is warm (repeat runs are then instant/deterministic)
- [ ] `python scripts/smoke.py` prints `OK`
- [ ] Backup screen recording of a clean run saved locally
- [ ] Deployed URLs (if used) tested from the venue network; free-tier backend pinged awake

## Modes

**Mode A - live** (primary): presenter speaks; AssemblyAI transcribes; signals appear live. Use a second device/tab (different name) for a two-person feel, or type lines for other speakers via the "speaking as" box.

**Mode B - controlled demo** (fallback): click **Run demo conversation**. Same engine and UI, scripted lines. Switch to it the moment the mic, network or STT misbehaves - the banner offers this.

## Suggested 3-minute flow

1. (15 s) Problem: "Transcripts tell you what was said, not what's happening in the conversation."
2. (20 s) Start conversation, show empty radar.
3. (90 s) Run/say the sequence below; point at the radar after each beat.
4. (30 s) Click the **Commitment changed** card - show Earlier/Later evidence and the "observable language only" note.
5. (20 s) End -> report: counts, timeline, click a timeline item.
6. (15 s) Close: "We're not just recording conversations. We're understanding how they evolve."

## Beats (what the demo script says)

| # | Speaker | Line | Expected signal |
|---|---|---|---|
| 1 | John | "Okay, for the release, I'll handle the deployment." | Commitment |
| 2 | Sarah | "I'm not sure we're actually ready for Friday." | Uncertainty |
| 3-4 | Michael / Maria | "We should use PostgreSQL..." / "I think MongoDB makes more sense here." | Unresolved disagreement |
| 5 | Maria | "I'm still concerned about authentication." | (first mention) |
| 6 | Sarah | "Yeah, I guess that could work for the timeline." | Hedged agreement |
| 8 | Maria | "The authentication service is still my biggest concern." | Repeated concern |
| 9 | Michael | "I'll prepare the deployment checklist." | Commitment |
| 10 | John | "Actually, I don't think I'll have enough time to handle the deployment." | **Commitment changed** |
| 11 | Maria | "...I'm worried the authentication changes could cause problems." | Repeated concern x3 |
| 12 | Sarah | "Who's going to handle the migration?" | (then nobody answers) |
| 13-14 | Michael / John | unrelated frontend chatter | **Unanswered question** |

Expected final report: 2 commitments, 1 uncertainty, 1 hedging, 1 commitment change, 1 repeated concern (x3), 1 disagreement, 1 unanswered question.

## Speaking live: phrases that reliably trigger signals

- "I'll handle the deployment." -> commitment
- "I'm not sure we're ready." -> uncertainty
- "I guess that could work." -> hedged agreement
- "I'm worried about the migration." (twice, different wording) -> repeated concern
- "Actually, I don't think I'll have enough time to handle the deployment." -> commitment change (say the earlier commitment first, same speaker, same topic word)
- "Who's going to handle the migration?" then change the subject twice -> unanswered question

## If something breaks

| Symptom | Do |
|---|---|
| Mic silent / STT banner | Click Run demo conversation |
| "Connection lost" | Wait - it auto-reconnects and re-syncs; if not, reload (room state is kept server-side) |
| LLM slow/down | Nothing - rules-only fallback is automatic; badge shows `rules-only` |
| Backend down | Play the backup recording |

## Judge-facing points

- Every signal shows its evidence; nothing is asserted about feelings or intent.
- Hybrid engine: deterministic rules + LLM refinement + memory of the conversation.
- Works without a conferencing vendor; the engine is provider-independent (Meet/Zoom/Teams are future adapters).
