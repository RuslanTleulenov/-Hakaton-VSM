"""Тесты геймификации и интеграций через HTTP: рейс, челлендж, выгрузка."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def client(tmp_path, monkeypatch):
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


def play(client, run, option_ids):
    body = run
    for option_id in option_ids:
        response = client.post(f"/api/v1/runs/{run['run_id']}/choose", json={"option_id": option_id})
        assert response.status_code == 200, response.text
        body = response.json()
    return body


def test_trip_runs_three_incidents_and_carries_memory(client):
    trips = client.get("/api/v1/trips").json()
    assert {t["id"] for t in trips} == {"day-751", "evening-763"}

    run = client.post("/api/v1/runs", json={"login": "test.user", "trip_id": "day-751"}).json()
    assert run["trip"]["position"] == 1 and run["trip"]["total"] == 3

    after_first = play(client, run, ["both", "upgrade", "thanks"])
    assert after_first["segment_done"]["scenario_id"] == "double-seat"
    assert after_first["trip"]["position"] == 2
    assert any("Салон на вашей стороне" in m["label"] for m in after_first["trip"]["memory"])
    assert after_first["scenario"]["id"] == "lost-child"
    carried_loyalty = after_first["loyalty"]

    after_second = play(client, run, ["child_first", "report_child", "distract", "calm_mother"])
    assert after_second["scenario"]["id"] == "medical"
    assert after_second["loyalty"] >= carried_loyalty - 10      # шкала продолжается, а не сбрасывается

    options = {o["id"] for o in after_second["node"]["options"]}
    assert options, "третий инцидент должен начаться"

    final = play(client, run, ["ask", "radio", "empathy", "neighbour_help"])
    assert final["finished"]
    assert len(final["result"]["segments"]) == 3
    assert any(a["id"] == "full-trip" for a in final["result"]["earned_achievements"])

    debrief = client.get(f"/api/v1/runs/{run['run_id']}/debrief").json()
    assert [p["scenario_id"] for p in debrief["parts"]] == ["double-seat", "lost-child", "medical"]
    assert debrief["trip"]["id"] == "day-751"


def test_debrief_shows_alternative_for_weak_choice(client):
    run = client.post("/api/v1/runs", json={"login": "test.user", "scenario_id": "medical"}).json()
    body = play(client, run, ["pills"])
    assert body["event"]["alternative"]["option_id"] == "ask"
    assert body["event"]["better"]


def test_challenge_is_the_same_scenario_for_everyone(client):
    first = client.get("/api/v1/challenge").json()
    second = client.get("/api/v1/challenge?login=test.user").json()
    assert first["scenario"]["id"] == second["scenario"]["id"]
    assert second["played"] is False

    run = client.post(
        "/api/v1/runs",
        json={"login": "test.user", "scenario_id": first["scenario"]["id"], "challenge": True},
    ).json()
    scenario = run["scenario"]["id"]
    assert scenario == first["scenario"]["id"]

    # Доигрываем челлендж любым доступным путём — важен сам факт зачёта.
    body = run
    while not body["finished"]:
        option = body["node"]["options"][0]["id"]
        body = client.post(f"/api/v1/runs/{run['run_id']}/choose", json={"option_id": option}).json()

    after = client.get("/api/v1/challenge?login=test.user").json()
    assert after["played"] is True
    assert after["leaderboard"][0]["login"] == "test.user"


def test_streak_and_expiring_points(client):
    run = client.post("/api/v1/runs", json={"login": "test.user", "scenario_id": "medical"}).json()
    play(client, run, ["ask", "radio", "empathy", "breathing"])
    streak = client.get("/api/v1/conductors/test.user/streak").json()
    assert streak["streak_days"] == 1
    assert streak["expiring"]["days_left"] == streak["expiring"]["expires_after_days"]


def test_trend_reports_competence_dynamics(client):
    for _ in range(2):
        run = client.post("/api/v1/runs", json={"login": "test.user", "scenario_id": "medical"}).json()
        play(client, run, ["ask", "radio", "empathy", "breathing"])
    trend = client.get("/api/v1/analytics/trend?login=test.user").json()
    assert len(trend["points"]) == 2
    assert {c["key"] for c in trend["competences"]} == {
        "safety",
        "deescalation",
        "service",
        "composure",
        "teamwork",
    }


def test_integration_requires_token(client):
    assert client.get("/api/v1/integration/progress").status_code == 422   # заголовка нет вовсе
    assert client.get("/api/v1/integration/progress", headers={"X-API-Key": "unknown-token"}).status_code == 401


def test_integration_export_and_assign(client):
    from app.main import conn

    conn.execute("INSERT INTO api_clients (name, token) VALUES ('HR-тест', 'secret-token')")
    conn.commit()
    headers = {"X-API-Key": "secret-token"}

    run = client.post("/api/v1/runs", json={"login": "test.user", "scenario_id": "medical"}).json()
    play(client, run, ["ask", "radio", "empathy", "breathing"])

    export = client.get("/api/v1/integration/progress", headers=headers).json()
    assert export["client"] == "HR-тест"
    row = export["conductors"][0]
    assert row["login"] == "test.user" and row["runs_completed"] == 1
    assert "display_name" not in row        # ФИО во внешнюю систему не уходит

    assigned = client.post(
        "/api/v1/integration/assign",
        headers=headers,
        json={"login": "test.user", "trip_id": "evening-763"},
    )
    assert assigned.status_code == 200
    titles = [n["title"] for n in client.get("/api/v1/notifications?login=test.user").json()]
    assert any("Вечерний рейс 763" in title for title in titles)
