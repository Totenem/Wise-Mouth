import re
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from ..config import settings
from ..models import db
from ..services import auth

router = APIRouter()

_USERNAME = re.compile(r"^[A-Za-z0-9_.-]{3,40}$")


class Credentials(BaseModel):
    username: str
    password: str


def current_user(authorization: str | None = Header(default=None)) -> dict:
    token = authorization[7:] if authorization and authorization.lower().startswith("bearer ") else None
    user = db.get_user(uid) if (uid := auth.user_id_from_token(token)) else None
    if user is None:
        raise HTTPException(401, "not signed in")
    return user


def _session(user: dict) -> dict:
    return {"token": auth.make_token(user["id"]), "user": {"id": user["id"], "username": user["username"]}}


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/api/config")
def config(request: Request):
    llm = request.app.state.llm
    return {"stt": bool(settings.assemblyai_api_key), "llm": llm.name, "llm_status": llm.status}


@router.post("/api/auth/register")
def register(body: Credentials):
    username = body.username.strip()
    if not _USERNAME.match(username):
        raise HTTPException(400, "username must be 3-40 letters, numbers, . _ -")
    if len(body.password) < 8:
        raise HTTPException(400, "password must be at least 8 characters")
    uid = uuid.uuid4().hex
    if not db.create_user(uid, username.lower(), auth.hash_password(body.password)):
        raise HTTPException(409, "username already taken")
    return _session({"id": uid, "username": username.lower()})


@router.post("/api/auth/login")
def login(body: Credentials):
    user = db.get_user_by_name(body.username.strip().lower())
    if user is None or not auth.verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "invalid username or password")
    return _session(user)


@router.get("/api/auth/me")
def me(user: dict = Depends(current_user)):
    return user


@router.get("/api/conversations")
def conversations(user: dict = Depends(current_user)):
    return db.list_conversations(user["id"])


@router.get("/api/conversations/{cid}")
def conversation(cid: str, request: Request, user: dict = Depends(current_user)):
    room = request.app.state.rooms.rooms.get(cid)
    if room is not None:
        if room.owner_id != user["id"]:
            raise HTTPException(404, "conversation not found")
        snap = room.snapshot()
        return {"id": cid, "status": room.status, "transcript": snap["transcript"], "signals": snap["signals"],
                "counts": snap["counts"]}
    data = db.load_conversation(cid, user["id"])
    if data is None:
        raise HTTPException(404, "conversation not found")
    return data
