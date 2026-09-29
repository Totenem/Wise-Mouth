import time

from fastapi.testclient import TestClient

from app.main import app


def test_typed_utterances_flow_through_pipeline(tmp_path, monkeypatch):
    with TestClient(app) as client:
        with client.websocket_connect("/ws/meeting/testroom") as ws:
            ws.send_json({"type": "join", "name": "John"})
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
        r = client.get("/api/conversations/testroom")
        assert r.status_code == 200 and r.json()["status"] == "ended"
