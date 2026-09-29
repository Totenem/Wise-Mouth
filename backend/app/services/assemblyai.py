"""AssemblyAI realtime (v3 streaming) session, one per participant.

Verify endpoint/params against current AssemblyAI docs if behaviour changes.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Awaitable, Callable
from urllib.parse import urlencode

from websockets.asyncio.client import connect

from ..config import settings

log = logging.getLogger("wisemouth.stt")
TextCb = Callable[[str], Awaitable[None]]


class AssemblyAISession:
    def __init__(self, on_partial: TextCb, on_final: TextCb, on_error: TextCb,
                 url: str | None = None, api_key: str | None = None):
        self.on_partial, self.on_final, self.on_error = on_partial, on_final, on_error
        self.url = url or settings.assemblyai_ws_url
        self.api_key = api_key or settings.assemblyai_api_key
        self._ws = None
        self._task: asyncio.Task | None = None
        self._closed = False
        self.ready = asyncio.Event()

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        backoff = 1.0
        params = urlencode({"sample_rate": 16000, "encoding": "pcm_s16le", "format_turns": "true"})
        while not self._closed:
            try:
                async with connect(f"{self.url}?{params}", additional_headers={"Authorization": self.api_key}) as ws:
                    self._ws = ws
                    self.ready.set()
                    backoff = 1.0
                    async for raw in ws:
                        await self._handle(raw)
            except Exception as e:
                self.ready.clear()
                self._ws = None
                if self._closed:
                    return
                log.warning("AssemblyAI connection lost: %s", e)
                await self.on_error(f"Speech connection lost, retrying ({e.__class__.__name__})")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 8.0)

    async def _handle(self, raw) -> None:
        msg = json.loads(raw)
        if msg.get("type") != "Turn":
            return
        text = (msg.get("transcript") or "").strip()
        if not text:
            return
        if msg.get("end_of_turn") and msg.get("turn_is_formatted", True):
            await self.on_final(text)
        elif not msg.get("end_of_turn"):
            await self.on_partial(text)

    async def send_audio(self, data: bytes) -> None:
        if self._ws is not None:
            try:
                await self._ws.send(data)
            except Exception:
                pass  # reconnect loop handles it; drop the frame

    async def close(self) -> None:
        self._closed = True
        if self._ws is not None:
            try:
                await self._ws.send(json.dumps({"type": "Terminate"}))
                await self._ws.close()
            except Exception:
                pass
        if self._task:
            self._task.cancel()
