"""End-to-end smoke test against a running backend.

Plays the deterministic demo conversation over the real WebSocket, ends the
session, and asserts the expected signals. Usage:

    python scripts/smoke.py [http://localhost:8000]
"""
import asyncio
import json
import sys
import uuid
from collections import Counter

import websockets

EXPECTED = {
    "commitment": 2, "uncertainty": 1, "hedging": 1, "commitment_change": 1,
    "repeated_concern": 1, "disagreement": 1, "unanswered_question": 1,
}


async def main(base: str) -> int:
    room = "smoke" + uuid.uuid4().hex[:6]
    url = base.replace("http", "ws", 1) + f"/ws/meeting/{room}"
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"type": "join", "name": "Smoke"}))
        await ws.send(json.dumps({"type": "demo_start", "speed": 10}))
        while json.loads(await asyncio.wait_for(ws.recv(), 60))["type"] != "demo_finished":
            pass
        await asyncio.sleep(1.0)
        await ws.send(json.dumps({"type": "end"}))
        while True:
            msg = json.loads(await asyncio.wait_for(ws.recv(), 20))
            if msg["type"] == "session_ended":
                break
    counts = Counter(s["type"] for s in msg["signals"] if s["status"] == "active")
    print("room:", room)
    print("counts:", dict(counts))
    bad = {k: (counts.get(k, 0), v) for k, v in EXPECTED.items() if counts.get(k, 0) != v}
    if bad:
        print("FAIL (got, expected):", bad)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000")))
