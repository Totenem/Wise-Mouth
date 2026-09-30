# 13 Demo video script (solo recording)

Target length: **3:00**. Record the screen plus your voiceover (OBS, or Win+Alt+R Xbox Game Bar, or Loom). You do not need teammates: the app has a built-in multi-speaker demo and a "speaking as" box, so one person can play every participant.

## Recording plan: three takes, then stitch

| Take | What | Why |
|---|---|---|
| A | Scripted demo (**Run demo conversation**) with your voiceover | Deterministic, always shows all 7 signals |
| B | Live typing as multiple speakers (the "speaking as" box) | Proves it is not pre-rendered |
| C | (Optional) Real mic, one sentence, if the AssemblyAI key works | Shows live STT. Skip if flaky |

Record voiceover **after** the screen capture if you stumble live. Play the screen video and narrate over it. Cut the final in CapCut / Clipchamp / DaVinci.

## Pre-flight (10 min)

- [ ] `docker compose up --build`, open http://localhost:3000 (or the deployed URL)
- [ ] `curl localhost:8000/api/config` shows the flags you expect
- [ ] Browser at 100% zoom, full screen, bookmarks bar hidden, notifications off (Focus Assist on)
- [ ] Log in / create a fresh room so History is not cluttered
- [ ] Do one dry run of the demo, then start a **new** conversation for the take
- [ ] Have this script open on a second monitor or phone

## Script

Times are cumulative. **[ACTION]** = what you do on screen. *Voiceover* = what you say.

### 0:00 Hook and problem (15 s)
**[ACTION]** Title slide or the landing page.
*"A transcript tells you what people said. It doesn't tell you what's actually happening in the conversation. Someone agrees, but hesitantly. Someone commits, then quietly backs out. A question goes unanswered. These moments get lost. WiseMouth makes them visible, in real time."*

### 0:15 Start a conversation (15 s)
**[ACTION]** Enter your name, click **Start Conversation**. Radar is empty.
*"This is a live meeting room. Speech goes through AssemblyAI streaming, and on the right is the Conversation Radar. It's empty. Let's run a team meeting."*

### 0:30 Run the demo (90 s)
**[ACTION]** Click **Run demo conversation**. Point the cursor at the radar after each beat.

| Beat | Say (over the playing demo) | Point at |
|---|---|---|
| John: "I'll handle the deployment." | *"John takes ownership: a commitment."* | Commitment counter +1 |
| Sarah: "I'm not sure we're actually ready for Friday." | *"Sarah signals uncertainty. Evidence is quoted right in the transcript."* | Chip on the line |
| Michael vs Maria: PostgreSQL / MongoDB | *"Two people propose competing options. No decision. That's an unresolved disagreement."* | Disagreement counter |
| Sarah: "Yeah, I guess that could work." | *"She agrees, but 'I guess' is weakened commitment: hedged agreement."* | Hedging chip |
| Maria: authentication concern (x2, x3) | *"The same concern, raised again and again. WiseMouth groups them by topic and counts."* | Repeated concern count |
| John: "I don't think I'll have enough time to handle the deployment." | *"Here's the one I care about most. John said he'd handle deployment. Now he says he probably can't. WiseMouth connects those two moments."* | Commitment changed card |
| Sarah: "Who's going to handle the migration?" then chatter | *"A question, and nobody answers it. Flagged as unanswered."* | Unanswered question |

Tip: the demo runs about 35 to 40 s at normal speed. If you need more narration time, pause between beats in the edit rather than talking fast.

### 2:00 Evidence drawer (30 s)
**[ACTION]** Click the **Commitment changed** card. The drawer opens.
*"Every signal shows its evidence: the earlier statement at 00:01, the later one at 00:28, the confidence, and the topic. And a note: this is observable language only. We never claim to read emotions, detect lies, or know intent."*

### 2:30 Live input proof (20 s) — Take B
**[ACTION]** Use the "speaking as" box. Type as "Alex": `I'll handle the migration.` Then as "Alex": `I won't be able to get to the migration this week.`
*"And it's not scripted. I'll type as a new speaker. A commitment... and then a retraction. Caught instantly."*

(If mic works, say the two sentences aloud instead. Cut the take if it's laggy.)

### 2:50 Report and close (20 s)
**[ACTION]** Click **End & view report**. Show counts, timeline, click one timeline item.
*"When the meeting ends, you get a report: what signals appeared, when, and the evidence. We're not just recording conversations. We're understanding how they evolve. This is WiseMouth."*

## Solo-presenter notes

- **Only one person?** The demo mode plays John, Sarah, Michael and Maria for you. Say this in the video: "the demo simulates four participants through the exact same engine as live speech" (true: `demo_script.py` pushes lines through `Room.final()`).
- **Live mic with two people:** open a second tab under a different name in an incognito window. Mute one tab to avoid echo.
- **Don't over-claim.** Say "rules plus LLM refinement" only if the LLM key was on during recording (check the `rules-only` / LLM badge). Otherwise say "rules-based detection, LLM refinement optional".
- **Mistakes:** just restart the room. Recordings are easy; keep takes short.

## Phrases for live speaking

- "I'll handle the deployment." -> commitment
- "I'm not sure we're ready." -> uncertainty
- "I guess that could work." -> hedged agreement
- "I'm worried about the migration." (twice, different wording) -> repeated concern
- "Actually, I don't think I'll have enough time to handle the deployment." -> commitment change (say the original commitment first, same speaker, same topic word)
- "Who's going to handle the migration?" then change the subject twice -> unanswered question

## Post-production checklist

- [ ] Trim dead air, keep it under 3:00 (or whatever the submission limit is)
- [ ] Add captions (auto-caption in CapCut/YouTube, then fix product names)
- [ ] Audio: record in a quiet room, normalize volume, no background music louder than -25 dB
- [ ] Export 1080p MP4; watch it once fully on a different device
- [ ] Save a copy as the backup recording (see the runbook checklist)
