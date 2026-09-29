"""Deterministic demo conversation (Mode B).

Lines are pushed through Room.final(), i.e. the exact same pipeline as live
speech: rules -> LLM refine -> conversation state -> radar. Nothing is pre-rendered.
"""
from __future__ import annotations

import asyncio

# (speaker, text, pause_before_seconds)
DEMO_LINES: list[tuple[str, str, float]] = [
    ("John", "Okay, for the release, I'll handle the deployment.", 1.0),
    ("Sarah", "I'm not sure we're actually ready for Friday.", 2.0),
    ("Michael", "We should use PostgreSQL for the new service.", 2.0),
    ("Maria", "I think MongoDB makes more sense here.", 2.0),
    ("Maria", "I'm still concerned about authentication.", 2.5),
    ("Sarah", "Yeah, I guess that could work for the timeline.", 2.0),
    ("Michael", "I still prefer PostgreSQL.", 2.0),
    ("Maria", "The authentication service is still my biggest concern.", 2.5),
    ("Michael", "I'll prepare the deployment checklist.", 2.0),
    ("John", "Actually, I don't think I'll have enough time to handle the deployment.", 3.0),
    ("Maria", "Honestly I'm worried the authentication changes could cause problems.", 2.5),
    ("Sarah", "Who's going to handle the migration?", 3.0),
    ("Michael", "Let's move on to the frontend work.", 2.5),
    ("John", "The frontend demo looks good so far.", 2.5),
]


async def _type_out(room, speaker: str, text: str) -> None:
    words = text.split()
    step = max(1, len(words) // 4)
    for i in range(step, len(words), step):
        await room.partial(speaker, " ".join(words[:i]))
        await asyncio.sleep(0.22)


async def run_demo(room, speed: float = 1.0) -> None:
    for speaker, text, pause in DEMO_LINES:
        await asyncio.sleep(pause / speed)
        await _type_out(room, speaker, text)
        await room.final(speaker, text)
    await room.broadcast({"type": "demo_finished"})
