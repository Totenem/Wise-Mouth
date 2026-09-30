# 14 Slide deck script

Target: **10 slides, ~5 minutes** speaking. One idea per slide, few words on the slide, the detail goes in the speaker notes. Screenshots already exist in `docs/assets/` (`meeting.png`, `evidence-drawer.png`, `report.png`).

Suggested look: dark background, one accent colour, big type (title 40pt+, body 24pt+). Fonts: Inter or Calibri.

---

## Slide 1 — Title
**On slide:** WiseMouth · *See what the conversation doesn't explicitly say.* · Your name / team / event
**Visual:** logo or `meeting.png` faded in the background
**Notes:** "Hi, I'm [name]. WiseMouth is a real-time conversation intelligence layer. I built it solo."

## Slide 2 — The problem
**On slide:** "Transcripts tell you what was said. Not what's happening."
Three short bullets:
- Agreement that isn't really agreement
- Commitments that quietly change
- Questions nobody answers
**Notes:** "Meeting tools give us transcripts, summaries and action items. But the important stuff hides in how the conversation progresses. Someone says 'I guess that works' and it gets logged as agreement. Someone commits, then backs out ten minutes later, and no one connects the two."

## Slide 3 — The solution
**On slide:** WiseMouth surfaces **observable language signals**, live, **with evidence**.
**Visual:** `meeting.png` (radar on the right)
**Notes:** "WiseMouth listens to a conversation and flags seven kinds of signals as they happen. Each comes with the exact words that triggered it."

## Slide 4 — The 7 signals
**On slide:** table of signal, example

| Signal | Example |
|---|---|
| Uncertainty | "I'm not sure we're ready for Friday." |
| Hedged agreement | "Yeah, I guess that could work." |
| Commitment | "I'll handle the deployment." |
| **Commitment changed** | "I don't think I'll have enough time." |
| Repeated concern | "...still my biggest concern." |
| Unresolved disagreement | PostgreSQL vs MongoDB, no decision |
| Unanswered question | "Who's going to handle the migration?" |

**Notes:** "The differentiator is the temporal ones. Connecting John's commitment at 00:01 to his retraction at 00:28 is the product."

## Slide 5 — How it works (architecture)
**On slide:** a left-to-right flow diagram:
`Mic / typed text` → `AssemblyAI streaming STT` → `Rules engine (candidates)` → `LLM refine (Groq → Gemini)` → `Conversation state (memory)` → `WebSocket` → `Live radar UI`
Caption: **AssemblyAI hears it. Rules detect it. The LLM understands it. State connects it. WiseMouth makes it visible.**
**Notes:** "Rules are cheap and deterministic. They nominate candidates. An LLM refines the ambiguous ones. A conversation-state layer remembers who committed to what, so later statements can be connected. If the LLM is down, rules-only keeps working."

## Slide 6 — Live demo (video)
**On slide:** full-bleed embedded demo video (or a "Live demo" title if presenting live)
**Notes:** "Here's a four-person meeting, simulated through the exact same pipeline as live speech." Let the video play (see `13-demo-video-script.md`). Mention the moment the commitment change appears.

## Slide 7 — Evidence-first, not mind-reading
**On slide:** "We never claim to read emotions, detect lies, or know intent."
**Visual:** `evidence-drawer.png`
Bullets: verbatim evidence · timestamp · confidence · earlier statement
**Notes:** "Every signal is explainable. The UI says 'uncertainty language detected', never 'Sarah is nervous'. That keeps it trustworthy and safe for sensitive settings."

## Slide 8 — Report
**On slide:** "After the conversation: a timeline you can act on."
**Visual:** `report.png`
**Notes:** "At the end you get counts, a signal-mix chart, a chronological timeline and an annotated transcript. Past conversations live in History."

## Slide 9 — Tech and status
**On slide:** two columns
- **Stack:** Next.js · TypeScript · Tailwind · Recharts | FastAPI · WebSockets · SQLAlchemy | Postgres | AssemblyAI · Groq/Gemini | Docker
- **Status:** 31 backend tests passing · end-to-end smoke test · auth + loading states · [deployed URL if applicable]
**Notes:** Be honest about what is verified. Mention what you have tested with real credentials and what not (see `11-status-and-roadmap.md`).

## Slide 10 — Where this goes next + close
**On slide:** Roadmap: Meet/Zoom/Teams adapters · real diarization · multi-language · retention/redaction controls · a care-team setting for patient conversations *(tie to your team's mission if relevant)*
Closing line, big: **"We're not just recording conversations. We're understanding how they evolve."**
**Notes:** "The engine is provider-independent; conferencing platforms are just adapters that feed it. Thank you." Add repo/demo link and your contact.

---

## Optional backup slides (after the close)

- **Q&A: accuracy?** Lexicon plus LLM. Known limits: English only, sarcasm invisible, heuristic answer detection. Roadmap has a labelled evaluation set.
- **Q&A: privacy?** No emotion or voice analysis, no profiling, retention controls on the roadmap.
- **Q&A: why not a summary tool?** Summaries flatten the progression. We keep it as a sequence of connected signals.

## Timing guide

| Slides | Time |
|---|---|
| 1-3 | 60 s |
| 4-5 | 60 s |
| 6 (demo) | 100 s |
| 7-8 | 50 s |
| 9-10 | 30 s |

## Before you present

- [ ] Confirm the event's time limit and trim slides 4/9 if needed
- [ ] Export as PDF as a backup
- [ ] Embed the video locally (don't rely on Wi-Fi)
- [ ] Take fresh screenshots if the UI changed since `docs/assets/`
