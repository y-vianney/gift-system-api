from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from gift_system.api import app
from gift_system.services.santa_service import build_and_save_assignments


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = tmp_path / "api_test.db"
    monkeypatch.setattr("gift_system.config.DB_FILE", db_path)
    monkeypatch.setattr("gift_system.storage.database.DB_FILE", db_path)
    monkeypatch.setattr("gift_system.services.santa_service.DB_FILE", db_path)

    # Populate dummy assignments
    emp_file = tmp_path / "employees.txt"
    emp_file.write_text(
        "GiverUser|giver@test.com|active|public\n"
        "ChildUser|child@test.com|active|public\n",
        encoding="utf-8",
    )
    keys = build_and_save_assignments(emp_file, send_emails=False, force_reset=True)

    with TestClient(app) as test_client:
        test_client.app_keys = {mail: (name, k, rec) for name, mail, k, rec in keys}  # type: ignore
        yield test_client


def test_api_ping(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json().get("status") == "ok"


def test_api_html_ui(client):
    res = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "SECRET SANTA" in res.text


def test_api_legacy_worker_name(client):
    giver_name, giver_key, target_name = client.app_keys["giver@test.com"]  # type: ignore

    res = client.post("/worker-name", json={"key": giver_key})
    assert res.status_code == 200
    assert res.json() == {"worker_name": target_name}

    # Invalid key
    bad_res = client.post("/worker-name", json={"key": "ZZ999"})
    assert bad_res.status_code == 404


def test_api_session_and_messaging_flow(client):
    giver_name, giver_key, target_name = client.app_keys["giver@test.com"]  # type: ignore
    target_mail = "child@test.com"
    target_name, target_key, _ = client.app_keys[target_mail]  # type: ignore

    # 1. Login as Giver (Santa)
    res_santa = client.post("/api/auth/session", json={"key": giver_key})
    assert res_santa.status_code == 200
    data_santa = res_santa.json()
    assert data_santa["participant_name"] == "GiverUser"
    assert data_santa["santa_mission"]["target_name"] == "ChildUser"
    thread_id = data_santa["santa_mission"]["thread_id"]

    # 2. Santa posts a message
    post_res = client.post(
        f"/api/threads/{thread_id}/messages",
        json={"key": giver_key, "content": "Hello de ton Père Noël !"},
    )
    assert post_res.status_code == 200
    assert post_res.json()["sender_role"] == "SANTA"
    assert post_res.json()["is_mine"] is True

    # 3. Target (Child) logs in
    res_child = client.post("/api/auth/session", json={"key": target_key})
    assert res_child.status_code == 200
    data_child = res_child.json()
    assert data_child["participant_name"] == "ChildUser"
    assert data_child["child_mission"]["thread_id"] == thread_id

    # 4. Child reads messages
    get_res = client.get(f"/api/threads/{thread_id}/messages?key={target_key}")
    assert get_res.status_code == 200
    messages = get_res.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello de ton Père Noël !"
    assert messages[0]["sender_display"] == "Père Noël 🎅"
    assert messages[0]["is_mine"] is False

    # 5. Child replies
    reply_res = client.post(
        f"/api/threads/{thread_id}/messages",
        json={"key": target_key, "content": "Merci Père Noël !"},
    )
    assert reply_res.status_code == 200
    assert reply_res.json()["sender_role"] == "CHILD"


def test_api_websocket_realtime(client):
    import json
    from starlette.websockets import WebSocketDisconnect

    giver_name, giver_key, target_name = client.app_keys["giver@test.com"]  # type: ignore
    target_name, target_key, _ = client.app_keys["child@test.com"]  # type: ignore

    res_santa = client.post("/api/auth/session", json={"key": giver_key})
    thread_id = res_santa.json()["santa_mission"]["thread_id"]

    # 1. Unauthorized connection rejected
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/threads/{thread_id}/ws?key=INVALIDKEY"):
            pass
    assert exc_info.value.code == 1008

    # 2. Authorized Santa connects
    with client.websocket_connect(f"/api/threads/{thread_id}/ws?key={giver_key}") as ws_santa:
        # Handshake message
        init_msg = json.loads(ws_santa.receive_text())
        assert init_msg["type"] == "connected"
        assert init_msg["role"] == "SANTA"

        # Ping-pong keepalive
        ws_santa.send_text(json.dumps({"type": "ping"}))
        pong_msg = json.loads(ws_santa.receive_text())
        assert pong_msg["type"] == "pong"

        # 3. HTTP POST triggers instant WebSocket broadcast
        client.post(
            f"/api/threads/{thread_id}/messages",
            json={"key": target_key, "content": "Coucou temps réel depuis l'enfant !"},
        )

        ws_broadcast = json.loads(ws_santa.receive_text())
        assert ws_broadcast["type"] == "new_message"
        assert ws_broadcast["message"]["content"] == "Coucou temps réel depuis l'enfant !"
        assert ws_broadcast["message"]["sender_role"] == "CHILD"

        # 4. Sending directly via WebSocket
        ws_santa.send_text(json.dumps({"content": "Réponse immédiate du Père Noël !"}))
        ws_reply = json.loads(ws_santa.receive_text())
        assert ws_reply["type"] == "new_message"
        assert ws_reply["message"]["content"] == "Réponse immédiate du Père Noël !"
        assert ws_reply["message"]["sender_role"] == "SANTA"

