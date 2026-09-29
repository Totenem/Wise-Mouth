from fastapi import APIRouter, HTTPException, Request

from ..config import settings
from ..models import db

router = APIRouter()


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/api/config")
def config(request: Request):
    llm = request.app.state.llm
    return {"stt": bool(settings.assemblyai_api_key), "llm": llm.name, "llm_status": llm.status}


@router.get("/api/conversations")
def conversations():
    return db.list_conversations()


@router.get("/api/conversations/{cid}")
def conversation(cid: str, request: Request):
    room = request.app.state.rooms.rooms.get(cid)
    if room is not None:
        snap = room.snapshot()
        return {"id": cid, "status": room.status, "transcript": snap["transcript"], "signals": snap["signals"],
                "counts": snap["counts"]}
    data = db.load_conversation(cid)
    if data is None:
        raise HTTPException(404, "conversation not found")
    return data
