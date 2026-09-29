"""WebSocket gateway: one connection per participant.

Client -> server: first message {"type":"join","name":...}; then binary PCM16 16kHz
frames, or JSON: mute/unmute, say, demo_start, end.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.demo_script import run_demo

log = logging.getLogger("wisemouth.ws")
router = APIRouter()


@router.websocket("/ws/meeting/{room_id}")
async def meeting_ws(ws: WebSocket, room_id: str):
    await ws.accept()
    manager = ws.app.state.rooms
    participant = room = None
    try:
        join = await ws.receive_json()
        name = (join.get("name") or "Guest").strip()[:40] or "Guest"
        room = manager.get_or_create(room_id)
        participant = await room.join(name, ws)
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            if msg.get("bytes") is not None:
                if participant.stt and not participant.muted:
                    await participant.stt.send_audio(msg["bytes"])
                continue
            data = _parse(msg.get("text"))
            kind = data.get("type")
            if kind in ("mute", "unmute"):
                participant.muted = kind == "mute"
                await room.broadcast({"type": "participants", "participants": room.participant_list()})
            elif kind == "say":  # typed / speaker-selector input goes through the same pipeline
                text = (data.get("text") or "").strip()
                if text and room.status == "live":
                    await room.final((data.get("speaker") or participant.name)[:40], text[:1000])
            elif kind == "demo_start" and room.status == "live" and not (room.demo_task and not room.demo_task.done()):
                room.demo_task = asyncio.create_task(run_demo(room, float(data.get("speed", 1.0))))
            elif kind == "end":
                await room.end()
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception("ws error")
    finally:
        if room and participant:
            await room.leave(participant)


def _parse(text: str | None) -> dict:
    import json
    try:
        d = json.loads(text or "{}")
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}
