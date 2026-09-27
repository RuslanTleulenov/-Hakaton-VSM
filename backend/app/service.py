"""Прикладной слой: партии, профили, достижения, рейтинг, аналитика.

Связывает детерминированное ядро (`engine`) с хранилищем (`db`).
Время решения считает сервер: в БД лежит момент показа узла, и при выборе
разница берётся по серверным часам — клиент не может «подкрутить» таймер.
"""
from __future__ import annotations

import sqlite3
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from . import achievements as ach
from . import engine
from .db import dumps, loads
from .domain import COMPETENCES, Scenario

# Уровни проводника по опыту: стажёр → наставник.
LEVELS = [
    (0, "Стажёр"),
    (300, "Проводник"),
    (900, "Старший проводник"),
    (1800, "Инструктор"),
    (3000, "Наставник"),
]


def now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat()


def level_of(xp: int) -> dict[str, Any]:
    current = LEVELS[0]
    nxt = None
    for index, (threshold, name) in enumerate(LEVELS):
        if xp >= threshold:
            current = (threshold, name)
            nxt = LEVELS[index + 1] if index + 1 < len(LEVELS) else None
    return {
        "name": current[1],
        "xp": xp,
        "next_name": nxt[1] if nxt else None,
        "xp_to_next": (nxt[0] - xp) if nxt else 0,
    }


# --- профили ---------------------------------------------------------------


def ensure_conductor(conn: sqlite3.Connection, login: str, display_name: str, brigade: str, depot: str) -> dict:
    row = conn.execute("SELECT * FROM conductors WHERE login = ?", (login,)).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO conductors (login, display_name, brigade, depot) VALUES (?, ?, ?, ?)",
            (login, display_name, brigade, depot),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM conductors WHERE login = ?", (login,)).fetchone()
    return dict(row)


def get_conductor(conn: sqlite3.Connection, login: str) -> dict | None:
    row = conn.execute("SELECT * FROM conductors WHERE login = ?", (login,)).fetchone()
    return dict(row) if row else None


def profile(conn: sqlite3.Connection, login: str, catalog: list[dict]) -> dict | None:
    conductor = get_conductor(conn, login)
    if conductor is None:
        return None
    runs = conn.execute(
        "SELECT scenario_id, result, finished_at FROM runs WHERE conductor_id = ? AND finished = 1"
        " ORDER BY finished_at DESC",
        (conductor["id"],),
    ).fetchall()
    results = [loads(r["result"]) for r in runs]

    competences = {key: 0 for key in COMPETENCES}
    for result in results:
        for key, value in result["competences"].items():
            competences[key] = competences.get(key, 0) + value

    earned_rows = conn.execute(
        "SELECT achievement_id, earned_at FROM earned_achievements WHERE conductor_id = ?",
        (conductor["id"],),
    ).fetchall()
    earned = {row["achievement_id"]: row["earned_at"] for row in earned_rows}

    return {
        "login": conductor["login"],
        "display_name": conductor["display_name"],
        "brigade": conductor["brigade"],
        "depot": conductor["depot"],
        "level": level_of(conductor["xp"]),
        "runs_completed": len(results),
        "average_score": round(sum(r["score"] for r in results) / len(results)) if results else 0,
        "competences": competences,
        "competence_titles": COMPETENCES,
        "achievements": [
            {**a, "earned": a["id"] in earned, "earned_at": earned.get(a["id"])} for a in catalog
        ],
        "history": [
            {
                "scenario_id": row["scenario_id"],
                "finished_at": row["finished_at"],
                "score": result["score"],
                "grade": result["grade"],
                "loyalty": result["loyalty"],
                "safety": result["safety"],
            }
            for row, result in zip(runs, results)
        ],
    }


# --- партия ----------------------------------------------------------------


def _state_to_json(state: engine.RunState) -> str:
    payload = asdict(state)
    payload["flags"] = sorted(state.flags)
    payload["events"] = [asdict(e) for e in state.events]
    return dumps(payload)


def _state_from_json(raw: str) -> engine.RunState:
    payload = loads(raw)
    events = [engine.Event(**e) for e in payload.pop("events", [])]
    payload["flags"] = set(payload.get("flags", []))
    return engine.RunState(events=events, **payload)


def _node_view(scenario: Scenario, state: engine.RunState) -> dict:
    node = scenario.node(state.node_id)
    return {
        "node_id": node.id,
        "text": node.text,
        "speaker": node.speaker,
        "timer": node.timer,
        "critical": node.critical,
        "options": [
            {"id": o.id, "text": o.text, "step": o.step}
            for o in engine.available_options(scenario, state)
        ],
    }


def _run_view(run_id: str, scenario: Scenario, state: engine.RunState) -> dict:
    return {
        "run_id": run_id,
        "scenario": {
            "id": scenario.id,
            "title": scenario.title,
            "segment": scenario.segment,
            "minutes_to_stop": scenario.minutes_to_stop,
            "car_class": scenario.car_class,
        },
        "loyalty": state.loyalty,
        "safety": state.safety,
        "finished": state.finished,
        "node": None if state.finished else _node_view(scenario, state),
    }


def start_run(conn: sqlite3.Connection, login: str, scenario: Scenario) -> dict:
    conductor = get_conductor(conn, login)
    if conductor is None:
        raise LookupError(f"нет проводника {login!r}")
    state = engine.start(scenario)
    run_id = uuid.uuid4().hex
    conn.execute(
        "INSERT INTO runs (id, conductor_id, scenario_id, state, node_shown_at) VALUES (?, ?, ?, ?, ?)",
        (run_id, conductor["id"], scenario.id, _state_to_json(state), _iso(now())),
    )
    conn.commit()
    return _run_view(run_id, scenario, state)


def _load_run(conn: sqlite3.Connection, run_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        raise LookupError(f"партия {run_id!r} не найдена")
    return row


def choose(
    conn: sqlite3.Connection,
    run_id: str,
    scenario: Scenario,
    option_id: str | None,
    catalog: list[dict],
) -> dict:
    row = _load_run(conn, run_id)
    if row["finished"]:
        raise ValueError("партия уже завершена")
    state = _state_from_json(row["state"])
    shown_at = datetime.fromisoformat(row["node_shown_at"])
    seconds = (now() - shown_at).total_seconds()

    event = engine.choose(scenario, state, option_id, seconds)
    position = len(state.events)
    conn.execute(
        "INSERT INTO run_events (run_id, position, payload) VALUES (?, ?, ?)",
        (run_id, position, dumps(asdict(event))),
    )
    conn.execute(
        "UPDATE runs SET state = ?, node_shown_at = ? WHERE id = ?",
        (_state_to_json(state), _iso(now()), run_id),
    )

    view = _run_view(run_id, scenario, state)
    view["event"] = asdict(event)
    if state.finished:
        view["result"] = _finish(conn, row, scenario, state, catalog)
    conn.commit()
    return view


def _finish(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    scenario: Scenario,
    state: engine.RunState,
    catalog: list[dict],
) -> dict:
    result = engine.score(scenario, state)
    conn.execute(
        "UPDATE runs SET finished = 1, result = ?, finished_at = ? WHERE id = ?",
        (dumps(result), _iso(now()), row["id"]),
    )
    conn.execute("UPDATE conductors SET xp = xp + ? WHERE id = ?", (result["xp"], row["conductor_id"]))

    completed = conn.execute(
        "SELECT COUNT(*) AS n FROM runs WHERE conductor_id = ? AND finished = 1",
        (row["conductor_id"],),
    ).fetchone()["n"] + 1
    already = {
        r["achievement_id"]
        for r in conn.execute(
            "SELECT achievement_id FROM earned_achievements WHERE conductor_id = ?",
            (row["conductor_id"],),
        )
    }
    earned = ach.newly_earned(catalog, already, result, completed)
    for achievement in earned:
        conn.execute(
            "INSERT INTO earned_achievements (conductor_id, achievement_id, run_id) VALUES (?, ?, ?)",
            (row["conductor_id"], achievement["id"], row["id"]),
        )
        notify(
            conn,
            row["conductor_id"],
            "achievement",
            f"Новое достижение: {achievement['title']}",
            achievement["description"],
        )
    result["earned_achievements"] = earned
    return result


def debrief(conn: sqlite3.Connection, run_id: str, scenario: Scenario) -> dict:
    """Разбор рейса: каждое изменение шкал с причиной и «как было лучше»."""
    row = _load_run(conn, run_id)
    state = _state_from_json(row["state"])
    events = [asdict(e) for e in state.events]
    result = loads(row["result"]) if row["result"] else engine.score(scenario, state)
    return {
        "run_id": run_id,
        "scenario": {
            "id": scenario.id,
            "title": scenario.title,
            "segment": scenario.segment,
            "sources": scenario.sources,
        },
        "result": result,
        "competence_titles": COMPETENCES,
        "events": events,
        "advice": _advice(result),
    }


def _advice(result: dict) -> list[str]:
    """Содержательные выводы, а не «верно/неверно»."""
    out: list[str] = []
    if result["safety"] < 70:
        out.append(
            "Рейтинг безопасности просел: в спорных ситуациях сначала снимается риск "
            "(начальник поезда, ПТБ, медики к платформе), и только потом сервисная часть."
        )
    if result["loyalty"] < 60:
        out.append(
            "Лояльность низкая: правильные по регламенту действия звучали сухо. "
            "Начинайте с признания ситуации и заверяйте пассажира в конце."
        )
    if result["timeouts"]:
        out.append(
            f"Таймеров пропущено: {result['timeouts']}. Пауза в критическом узле — это выбор "
            "в пользу худшего развития событий."
        )
    for key in result["weak"]:
        out.append(f"Проседает компетенция «{COMPETENCES[key]}» — добавим сценарии на неё в следующий рейс.")
    if not out:
        out.append("Ровный рейс: обе шкалы удержаны, критические решения приняты вовремя.")
    return out


# --- рейтинг, аналитика, уведомления ---------------------------------------


def leaderboard(conn: sqlite3.Connection, scope: str = "company", value: str | None = None) -> list[dict]:
    query = (
        "SELECT c.login, c.display_name, c.brigade, c.depot, c.xp,"
        " COUNT(r.id) AS runs, COALESCE(ROUND(AVG(json_extract(r.result, '$.score'))), 0) AS avg_score"
        " FROM conductors c LEFT JOIN runs r ON r.conductor_id = c.id AND r.finished = 1"
    )
    params: tuple = ()
    if scope in {"brigade", "depot"} and value:
        query += f" WHERE c.{scope} = ?"
        params = (value,)
    query += " GROUP BY c.id ORDER BY c.xp DESC, avg_score DESC LIMIT 50"
    rows = conn.execute(query, params).fetchall()
    return [
        {**dict(row), "level": level_of(row["xp"])["name"], "place": index + 1}
        for index, row in enumerate(rows)
    ]


def hotspots(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    """Где ошибаются чаще всего: развилки с худшим средним эффектом на шкалы."""
    rows = conn.execute("SELECT r.scenario_id, e.payload FROM run_events e JOIN runs r ON r.id = e.run_id").fetchall()
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        event = loads(row["payload"])
        key = (row["scenario_id"], event["node_id"])
        bucket = buckets.setdefault(
            key,
            {"scenario_id": key[0], "node_id": key[1], "attempts": 0, "damage": 0, "timeouts": 0},
        )
        bucket["attempts"] += 1
        bucket["timeouts"] += int(event["timed_out"])
        bucket["damage"] += min(0, event["loyalty_delta"]) + min(0, event["safety_delta"])
    out = sorted(buckets.values(), key=lambda b: b["damage"])
    for bucket in out:
        bucket["avg_damage"] = round(bucket["damage"] / bucket["attempts"], 1)
    return out[:limit]


def notify(conn: sqlite3.Connection, conductor_id: int, kind: str, title: str, body: str) -> None:
    conn.execute(
        "INSERT INTO notifications (conductor_id, kind, title, body) VALUES (?, ?, ?, ?)",
        (conductor_id, kind, title, body),
    )


def notifications(conn: sqlite3.Connection, login: str) -> list[dict]:
    conductor = get_conductor(conn, login)
    if conductor is None:
        raise LookupError(f"нет проводника {login!r}")
    rows = conn.execute(
        "SELECT id, kind, title, body, read, created_at FROM notifications"
        " WHERE conductor_id = ? ORDER BY id DESC LIMIT 20",
        (conductor["id"],),
    ).fetchall()
    return [dict(row) for row in rows]


def mark_read(conn: sqlite3.Connection, notification_id: int) -> None:
    conn.execute("UPDATE notifications SET read = 1 WHERE id = ?", (notification_id,))
    conn.commit()


def recommended(conn: sqlite3.Connection, login: str, scenarios: dict[str, Scenario]) -> list[str]:
    """Адаптивный подбор: вперёд идут сценарии, которых нет в истории,
    затем те, что были пройдены хуже всего."""
    conductor = get_conductor(conn, login)
    if conductor is None:
        return list(scenarios)
    rows = conn.execute(
        "SELECT scenario_id, json_extract(result, '$.score') AS score FROM runs"
        " WHERE conductor_id = ? AND finished = 1",
        (conductor["id"],),
    ).fetchall()
    best: dict[str, int] = {}
    for row in rows:
        best[row["scenario_id"]] = max(best.get(row["scenario_id"], 0), int(row["score"] or 0))
    return sorted(scenarios, key=lambda sid: best.get(sid, -1))
