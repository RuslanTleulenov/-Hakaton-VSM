"""Тесты HTTP API на временной базе: партия целиком и поведение при ошибках."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Каждый тест работает со своей базой: стенд разработчика не трогаем."""
    from app import db

    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    for module in [m for m in list(sys.modules) if m.startswith("app.main")]:
        del sys.modules[module]
    from app.main import app

    with TestClient(app) as test_client:
        test_client.post(
            "/api/v1/conductors",
            json={
                "login": "test.user",
                "display_name": "Тестов Т.",
                "brigade": "Бригада 1",
                "depot": "Депо Тверь",
            },
        )
        yield test_client


def test_health_and_reference(client):
    assert client.get("/api/v1/health").json()["scenarios"] == 3
    reference = client.get("/api/v1/reference").json()
    assert "composure" in reference["competences"]
    assert "acknowledge" in reference["steps"]


def test_full_run_gives_debrief_profile_and_leaderboard(client):
    run = client.post("/api/v1/runs", json={"login": "test.user", "scenario_id": "medical"}).json()
    assert run["node"]["timer"] == 20

    for option_id in ["ask", "radio", "empathy", "breathing"]:
        response = client.post(f"/api/v1/runs/{run['run_id']}/choose", json={"option_id": option_id})
        assert response.status_code == 200
        body = response.json()
    assert body["finished"]
    assert body["result"]["grade"] == "Отлично"
    assert any(a["id"] == "first-run" for a in body["result"]["earned_achievements"])

    debrief = client.get(f"/api/v1/runs/{run['run_id']}/debrief").json()
    assert len(debrief["events"]) == 4
    assert all(event["reasons"] for event in debrief["events"])
    assert debrief["advice"]

    profile = client.get("/api/v1/conductors/test.user").json()
    assert profile["runs_completed"] == 1
    assert profile["level"]["xp"] > 0

    board = client.get("/api/v1/leaderboard").json()
    assert board[0]["login"] == "test.user"

    hotspots = client.get("/api/v1/analytics/hotspots").json()
    assert {h["node_id"] for h in hotspots} == {e["node_id"] for e in debrief["events"]}


def test_unknown_scenario_and_run_return_404(client):
    assert client.post("/api/v1/runs", json={"login": "test.user", "scenario_id": "нет"}).status_code == 404
    assert client.get("/api/v1/runs/deadbeef/debrief").status_code == 404
    assert client.get("/api/v1/conductors/нет-такого").status_code == 404


def test_option_blocked_by_flags_returns_409(client):
    run = client.post("/api/v1/runs", json={"login": "test.user", "scenario_id": "double-seat"}).json()
    client.post(f"/api/v1/runs/{run['run_id']}/choose", json={"option_id": "side"})
    blocked = client.post(f"/api/v1/runs/{run['run_id']}/choose", json={"option_id": "upgrade"})
    assert blocked.status_code == 409


def test_choice_in_finished_run_returns_409(client):
    run = client.post("/api/v1/runs", json={"login": "test.user", "scenario_id": "medical"}).json()
    for option_id in ["ask", "radio", "empathy", "breathing"]:
        client.post(f"/api/v1/runs/{run['run_id']}/choose", json={"option_id": option_id})
    late = client.post(f"/api/v1/runs/{run['run_id']}/choose", json={"option_id": "ask"})
    assert late.status_code == 409


def test_notifications_flow(client):
    empty = client.get("/api/v1/notifications?login=test.user").json()
    assert empty == []
    run = client.post("/api/v1/runs", json={"login": "test.user", "scenario_id": "medical"}).json()
    for option_id in ["ask", "radio", "empathy", "breathing"]:
        client.post(f"/api/v1/runs/{run['run_id']}/choose", json={"option_id": option_id})
    items = client.get("/api/v1/notifications?login=test.user").json()
    assert any(n["kind"] == "achievement" for n in items)         # ачивка приходит уведомлением
    assert client.post(f"/api/v1/notifications/{items[0]['id']}/read").status_code == 200
    assert client.get("/api/v1/notifications?login=test.user").json()[0]["read"] == 1


def test_leaderboard_scope_is_validated(client):
    assert client.get("/api/v1/leaderboard?scope=вселенная").status_code == 422
