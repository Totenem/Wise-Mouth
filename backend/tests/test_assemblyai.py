"""AssemblyAI session against a local fake streaming server (no key/network needed)."""
import asyncio
import json

from websockets.asyncio.server import serve

from app.services.assemblyai import AssemblyAISession


async def test_partials_finals_and_audio_relay():
    received_audio: list[bytes] = []
    auth: list[str] = []

    async def handler(ws):
        auth.append(ws.request.headers.get("Authorization", ""))
        await ws.send(json.dumps({"type": "Begin", "id": "x"}))
        audio = await ws.recv()
        received_audio.append(audio)
        await ws.send(json.dumps({"type": "Turn", "transcript": "I'll han", "end_of_turn": False}))
        # unformatted end-of-turn is ignored; the formatted one is final
        await ws.send(json.dumps({"type": "Turn", "transcript": "i'll handle it", "end_of_turn": True, "turn_is_formatted": False}))
        await ws.send(json.dumps({"type": "Turn", "transcript": "I'll handle it.", "end_of_turn": True, "turn_is_formatted": True}))
        await asyncio.sleep(0.3)

    partials, finals, errors = [], [], []

    async def on_partial(t): partials.append(t)
    async def on_final(t): finals.append(t)
    async def on_error(m): errors.append(m)

    async with serve(handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        s = AssemblyAISession(on_partial, on_final, on_error, url=f"ws://127.0.0.1:{port}", api_key="k123")
        await s.start()
        await asyncio.wait_for(s.ready.wait(), 3)
        await s.send_audio(b"\x00\x01" * 800)
        for _ in range(50):
            if finals:
                break
            await asyncio.sleep(0.05)
        await s.close()

    assert auth == ["k123"]
    assert received_audio == [b"\x00\x01" * 800]
    assert partials == ["I'll han"]
    assert finals == ["I'll handle it."]
