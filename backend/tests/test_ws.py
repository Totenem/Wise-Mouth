import time
import uuid

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


def _register(client, prefix="user"):
    r = client.post("/api/auth/register", json={"username": f"{prefix}_{uuid.uuid4().hex[:8]}", "password": "hunter2hunter2"})
    assert r.status_code == 200
    return r.json()["token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_typed_utterances_flow_through_pipeline(tmp_path, monkeypatch):
    with TestClient(app) as client:
        token = _register(client)
        with client.websocket_connect("/ws/meeting/testroom") as ws:
            ws.send_json({"type": "join", "name": "John", "token": token})
            snap = ws.receive_json()
            assert snap["type"] == "state_snapshot" and snap["you"] == "John"
            ws.send_json({"type": "say", "text": "I'll handle the deployment."})
            seen = []
            deadline = time.time() + 5
            while time.time() < deadline and "signal" not in seen:
                seen.append(ws.receive_json()["type"])
            assert "transcript_final" in seen and "signal" in seen
            ws.send_json({"type": "end"})
            while True:
                if ws.receive_json()["type"] == "session_ended":
                    break
        r = client.get("/api/conversations/testroom", headers=_auth(token))
        assert r.status_code == 200 and r.json()["status"] == "ended"


def test_history_is_separated_per_user():
    with TestClient(app) as client:
        alice, bob = _register(client, "alice"), _register(client, "bob")
        room = uuid.uuid4().hex[:8]
        with client.websocket_connect(f"/ws/meeting/{room}") as ws:
            ws.send_json({"type": "join", "name": "Alice", "token": alice})
            ws.receive_json()
            ws.send_json({"type": "end"})
            while ws.receive_json()["type"] != "session_ended":
                pass
        time.sleep(0.5)  # DB writes are fire-and-forget
        assert room in [c["id"] for c in client.get("/api/conversations", headers=_auth(alice)).json()]
        assert client.get("/api/conversations", headers=_auth(bob)).json() == []
        assert client.get(f"/api/conversations/{room}", headers=_auth(alice)).status_code == 200
        assert client.get(f"/api/conversations/{room}", headers=_auth(bob)).status_code == 404


def test_auth_required_and_login():
    with TestClient(app) as client:
        assert client.get("/api/conversations").status_code == 401
        assert client.get("/api/conversations", headers=_auth("garbage")).status_code == 401
        name = f"carol_{uuid.uuid4().hex[:8]}"
        assert client.post("/api/auth/register", json={"username": name, "password": "short"}).status_code == 400
        assert client.post("/api/auth/register", json={"username": name, "password": "longenough1"}).status_code == 200
        assert client.post("/api/auth/register", json={"username": name, "password": "longenough1"}).status_code == 409
        assert client.post("/api/auth/login", json={"username": name, "password": "wrongwrong"}).status_code == 401
        r = client.post("/api/auth/login", json={"username": name.upper(), "password": "longenough1"})
        assert r.status_code == 200
        assert client.get("/api/auth/me", headers=_auth(r.json()["token"])).json()["username"] == name


def test_guest_cannot_start_a_room():
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/meeting/guestroom") as ws:
                ws.send_json({"type": "join", "name": "Guest"})
                ws.receive_json()
