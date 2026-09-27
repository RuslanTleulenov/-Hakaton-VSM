"""Прикладной слой: партии, профили, достижения, рейтинг, аналитика.

Связывает детерминированное ядро (`engine`) с хранилищем (`db`).
Время решения считает сервер: в БД лежит момент показа узла, и при выборе
разница берётся по серверным часам — клиент не может «подкрутить» таймер.
"""
from __future__ import annotations

import sqlite3
import uuid
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from . import achievements as ach
from . import engine
from .db import dumps, loads
from .domain import COMPETENCES, Scenario
from .loader import Content

# Уровни проводника по опыту: стажёр → наставник.
# Пороги рассчитаны на реальный темп: за рейс начисляется балл × сложность,
# то есть 100–300 очков. «Проводник» — это 3–5 пройденных ситуаций,
# «Наставник» — примерно полсотни, то есть несколько месяцев регулярной работы
# с тренажёром, а не один вечер.
LEVELS = [
    (0, "Стажёр"),
    (600, "Проводник"),
    (2000, "Старший проводник"),
    (4500, "Инструктор"),
    (9000, "Наставник"),
]


def now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat()


def timestamp() -> str:
    """Метка времени сервера для выгрузок во внешние системы."""
    return _iso(now())


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
    scene = node.scene or scenario.scene
    character = scenario.characters.get(node.character) if node.character else None
    return {
        "node_id": node.id,
        "text": node.text,
        "speaker": node.speaker,
        "timer": node.timer,
        "critical": node.critical,
        # Слой новеллы: пути к ассетам считает сервер, интерфейс их просто
        # подставляет. Файла может не быть — тогда фронтенд рисует заглушку.
        "scene": scene,
        "scene_image": f"/static/assets/scenes/{scene}.jpg" if scene else None,
        "character": None
        if character is None
        else {
            "id": character.id,
            "name": character.name,
            "role": character.role,
            "mood": node.mood,
            "sprite": f"/static/assets/characters/{character.sprite}-{node.mood}.png",
        },
        "options": [
            {"id": o.id, "text": o.text, "step": o.step}
            for o in engine.available_options(scenario, state)
        ],
    }


def _run_view(run_id: str, content: Content, state: engine.RunState) -> dict:
    scenario = content.scenario(state.scenario_id)
    trip = content.trips.get(state.trip_id) if state.trip_id else None
    return {
        "run_id": run_id,
        "scenario": {
            "id": scenario.id,
            "title": scenario.title,
            "segment": scenario.segment,
            "minutes_to_stop": scenario.minutes_to_stop,
            "car_class": scenario.car_class,
        },
        "trip": None
        if trip is None
        else {
            "id": trip.id,
            "title": trip.title,
            "route": trip.route,
            "position": len(state.segments) + 1,
            "total": len(trip.segments),
            "left": list(state.queue),
            # Память рейса: только те флаги, которым рейс дал человеческое имя.
            "memory": [
                {"flag": flag, "label": label}
                for flag, label in trip.memory_labels.items()
                if flag in state.flags
            ],
        },
        "loyalty": state.loyalty,
        "safety": state.safety,
        "finished": state.finished,
        "node": None if state.finished else _node_view(scenario, state),
    }


def start_run(
    conn: sqlite3.Connection,
    login: str,
    content: Content,
    scenario_id: str | None = None,
    trip_id: str | None = None,
    challenge_week: str | None = None,
) -> dict:
    """Начать партию: отдельный инцидент (`scenario_id`) или рейс (`trip_id`)."""
    conductor = get_conductor(conn, login)
    if conductor is None:
        raise LookupError(f"нет проводника {login!r}")
    if trip_id:
        trip = content.trip(trip_id)
        state = engine.start_trip(trip, content.scenario(trip.segments[0]))
    elif scenario_id:
        state = engine.start(content.scenario(scenario_id))
    else:
        raise ValueError("нужен scenario_id или trip_id")

    run_id = uuid.uuid4().hex
    conn.execute(
        "INSERT INTO runs (id, conductor_id, scenario_id, trip_id, challenge_week, state, node_shown_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            run_id,
            conductor["id"],
            state.scenario_id,
            trip_id,
            challenge_week,
            _state_to_json(state),
            _iso(now()),
        ),
    )
    conn.commit()
    return _run_view(run_id, content, state)


def _load_run(conn: sqlite3.Connection, run_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        raise LookupError(f"партия {run_id!r} не найдена")
    return row


def choose(
    conn: sqlite3.Connection,
    run_id: str,
    content: Content,
    option_id: str | None,
) -> dict:
    """Ход проводника. Время решения берётся по серверным часам."""
    row = _load_run(conn, run_id)
    if row["finished"]:
        raise ValueError("партия уже завершена")
    state = _state_from_json(row["state"])
    scenario = content.scenario(state.scenario_id)
    shown_at = datetime.fromisoformat(row["node_shown_at"])
    seconds = (now() - shown_at).total_seconds()

    event = engine.choose(scenario, state, option_id, seconds)
    conn.execute(
        "INSERT INTO run_events (run_id, position, payload) VALUES (?, ?, ?)",
        (run_id, len(state.events), dumps(asdict(event))),
    )

    segment_done = None
    if state.finished and state.queue:
        # Инцидент закончился, но рейс продолжается: шкалы и память едут дальше.
        segment_done = {
            "scenario_id": scenario.id,
            "title": scenario.title,
            "ending": state.ending,
            "text": scenario.node(state.node_id).text,
        }
        engine.continue_trip(state, content.scenario(state.queue[0]))

    conn.execute(
        "UPDATE runs SET state = ?, scenario_id = ?, node_shown_at = ? WHERE id = ?",
        (_state_to_json(state), state.scenario_id, _iso(now()), run_id),
    )

    view = _run_view(run_id, content, state)
    view["event"] = asdict(event)
    view["segment_done"] = segment_done
    if state.finished:
        view["result"] = _finish(conn, row, content, state)
    conn.commit()
    return view


def _finish(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    content: Content,
    state: engine.RunState,
) -> dict:
    scenario = content.scenario(state.scenario_id)
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
    streak = streak_days(conn, row["conductor_id"], including_today=True)
    earned = ach.newly_earned(content.achievements, already, result, completed, streak)
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
    before = conn.execute("SELECT xp FROM conductors WHERE id = ?", (row["conductor_id"],)).fetchone()["xp"]
    _notify_level_up(conn, row["conductor_id"], before - result["xp"], before)
    result["earned_achievements"] = earned
    result["streak"] = streak
    return result


def _notify_level_up(conn: sqlite3.Connection, conductor_id: int, before: int, after: int) -> None:
    """Уведомление о новом уровне — только когда порог действительно пройден."""
    if level_of(before)["name"] != level_of(after)["name"]:
        notify(
            conn,
            conductor_id,
            "level_up",
            f"Новый уровень: {level_of(after)['name']}",
            f"Накоплено {after} очков опыта.",
        )


def debrief(conn: sqlite3.Connection, run_id: str, content: Content) -> dict:
    """Разбор рейса: каждое изменение шкал с причиной, альтернативой и выводом."""
    row = _load_run(conn, run_id)
    state = _state_from_json(row["state"])
    scenario = content.scenario(state.scenario_id)
    result = loads(row["result"]) if row["result"] else engine.score(scenario, state)
    trip = content.trips.get(row["trip_id"]) if row["trip_id"] else None

    # Ходы группируются по инцидентам: в рейсе их несколько.
    by_scenario: list[dict] = []
    for event in state.events:
        scenario_id = event.scenario_id or state.scenario_id
        if not by_scenario or by_scenario[-1]["scenario_id"] != scenario_id:
            part = content.scenario(scenario_id)
            by_scenario.append(
                {
                    "scenario_id": scenario_id,
                    "title": part.title,
                    "segment": part.segment,
                    "sources": part.sources,
                    "events": [],
                }
            )
        by_scenario[-1]["events"].append(asdict(event))

    return {
        "run_id": run_id,
        "trip": None if trip is None else {"id": trip.id, "title": trip.title, "route": trip.route},
        "scenario": {
            "id": scenario.id,
            "title": scenario.title,
            "segment": scenario.segment,
            "sources": scenario.sources,
        },
        "result": result,
        "competence_titles": COMPETENCES,
        "events": [asdict(event) for event in state.events],
        "parts": by_scenario,
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
    if len(result.get("segments", [])) > 1:
        bad = [s for s in result["segments"] if s.get("ending") == "bad"]
        if bad:
            out.append(
                "В рейсе несколько инцидентов подряд, и неудачный исход одного из них тянет "
                "за собой остальные: пассажиры помнят, как с ними обошлись на прошлом перегоне."
            )
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
        key = (event.get("scenario_id") or row["scenario_id"], event["node_id"])
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


def recommended(conn: sqlite3.Connection, login: str, content: Content) -> list[str]:
    """Адаптивный подбор: вперёд идут сценарии, которых нет в истории,
    затем те, что были пройдены хуже всего."""
    conductor = get_conductor(conn, login)
    if conductor is None:
        return list(content.scenarios)
    rows = conn.execute(
        "SELECT scenario_id, json_extract(result, '$.score') AS score FROM runs"
        " WHERE conductor_id = ? AND finished = 1",
        (conductor["id"],),
    ).fetchall()
    best: dict[str, int] = {}
    for row in rows:
        best[row["scenario_id"]] = max(best.get(row["scenario_id"], 0), int(row["score"] or 0))
    return sorted(content.scenarios, key=lambda sid: best.get(sid, -1))


# --- серии, рейс недели, сгорающие баллы ------------------------------------

# Баллы челленджа сгорают, если проводник не выходил на тренажёр столько дней.
POINTS_EXPIRE_DAYS = 7
CHALLENGE_BONUS_XP = 150


def _run_dates(conn: sqlite3.Connection, conductor_id: int) -> list[date]:
    rows = conn.execute(
        "SELECT DISTINCT date(finished_at) AS day FROM runs"
        " WHERE conductor_id = ? AND finished = 1 ORDER BY day DESC",
        (conductor_id,),
    ).fetchall()
    return [date.fromisoformat(row["day"]) for row in rows if row["day"]]


def streak_days(conn: sqlite3.Connection, conductor_id: int, including_today: bool = False) -> int:
    """Серия: сколько дней подряд проводник выходил на тренажёр.

    Серия не рвётся «вчерашним» днём: пока сегодня не закончилось, вчерашняя
    серия считается живой — иначе смена в ночь обнуляла бы прогресс.
    """
    days = set(_run_dates(conn, conductor_id))
    today = now().date()
    if including_today:
        days.add(today)
    if not days:
        return 0
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def current_week(moment: datetime | None = None) -> str:
    """ISO-неделя вида 2026-W40 — ключ челленджа «Рейс недели»."""
    iso = (moment or now()).isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def challenge(conn: sqlite3.Connection, content: Content, login: str | None = None) -> dict:
    """Рейс недели: один и тот же сценарий для всех — сравнение честное.

    Сценарий выбирается детерминированно по номеру недели, поэтому у всех
    бригад он совпадает и не зависит от того, кто первым открыл приложение.
    """
    week = current_week()
    order = sorted(content.scenarios)
    scenario_id = order[int(week.split("-W")[1]) % len(order)]
    scenario = content.scenario(scenario_id)

    board = conn.execute(
        "SELECT c.login, c.display_name, c.brigade,"
        " MAX(json_extract(r.result, '$.score')) AS best"
        " FROM runs r JOIN conductors c ON c.id = r.conductor_id"
        " WHERE r.finished = 1 AND r.challenge_week = ?"
        " GROUP BY c.id ORDER BY best DESC LIMIT 20",
        (week,),
    ).fetchall()

    played = False
    if login:
        conductor = get_conductor(conn, login)
        played = bool(
            conductor
            and conn.execute(
                "SELECT 1 FROM runs WHERE conductor_id = ? AND challenge_week = ? AND finished = 1",
                (conductor["id"], week),
            ).fetchone()
        )
    return {
        "week": week,
        "scenario": {"id": scenario.id, "title": scenario.title, "summary": scenario.summary},
        "bonus_xp": CHALLENGE_BONUS_XP,
        "played": played,
        "leaderboard": [
            {**dict(row), "place": index + 1} for index, row in enumerate(board)
        ],
    }


def expiring_points(conn: sqlite3.Connection, login: str) -> dict:
    """Сколько очков сгорит, если не выйти на тренажёр.

    Сгорают только очки челленджей за последнюю неделю — базовый опыт
    не отбирается: наказывать за отпуск тренажёр не должен.
    """
    conductor = get_conductor(conn, login)
    if conductor is None:
        raise LookupError(f"нет проводника {login!r}")
    row = conn.execute(
        "SELECT COALESCE(SUM(json_extract(result, '$.xp')), 0) AS points, MAX(finished_at) AS last"
        " FROM runs WHERE conductor_id = ? AND finished = 1 AND challenge_week IS NOT NULL",
        (conductor["id"],),
    ).fetchone()
    last_run = _run_dates(conn, conductor["id"])
    days_idle = (now().date() - last_run[0]).days if last_run else None
    left = None if days_idle is None else max(0, POINTS_EXPIRE_DAYS - days_idle)
    return {
        "points": int(row["points"] or 0),
        "days_idle": days_idle,
        "days_left": left,
        "expires_after_days": POINTS_EXPIRE_DAYS,
    }


def competence_trend(conn: sqlite3.Connection, login: str, limit: int = 10) -> dict:
    """Динамика компетенций по последним рейсам — видно, что растёт, а что нет."""
    conductor = get_conductor(conn, login)
    if conductor is None:
        raise LookupError(f"нет проводника {login!r}")
    rows = conn.execute(
        "SELECT scenario_id, finished_at, result FROM runs"
        " WHERE conductor_id = ? AND finished = 1 ORDER BY finished_at DESC LIMIT ?",
        (conductor["id"], limit),
    ).fetchall()
    results = [loads(row["result"]) for row in rows][::-1]
    points = [
        {
            "finished_at": row["finished_at"],
            "scenario_id": row["scenario_id"],
            "score": result["score"],
            "competences": result["competences"],
        }
        for row, result in zip(rows[::-1], results)
    ]
    half = len(results) // 2 or 1
    gaps = []
    for key, title in COMPETENCES.items():
        early = sum(r["competences"].get(key, 0) for r in results[:half])
        late = sum(r["competences"].get(key, 0) for r in results[-half:])
        gaps.append({"key": key, "title": title, "early": early, "late": late, "delta": late - early})
    return {"points": points, "competences": sorted(gaps, key=lambda g: g["delta"])}


# --- интеграция с внешними системами ---------------------------------------


def progress_export(
    conn: sqlite3.Connection,
    catalog: list[dict],
    depot: str | None = None,
    brigade: str | None = None,
) -> list[dict]:
    """Учебный прогресс для HR/LMS.

    В выгрузке нет персональных данных: учётная запись, подразделение и
    показатели обучения. ФИО сотрудника HR-система знает сама — тренажёру
    оно не нужно и потому не хранится.
    """
    query = "SELECT id, login, brigade, depot, xp FROM conductors"
    clauses, params = [], []
    if depot:
        clauses.append("depot = ?")
        params.append(depot)
    if brigade:
        clauses.append("brigade = ?")
        params.append(brigade)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    rows = conn.execute(query + " ORDER BY xp DESC", params).fetchall()

    out = []
    for row in rows:
        results = [
            loads(r["result"])
            for r in conn.execute(
                "SELECT result FROM runs WHERE conductor_id = ? AND finished = 1", (row["id"],)
            )
        ]
        competences = {key: 0 for key in COMPETENCES}
        for result in results:
            for key, value in result["competences"].items():
                competences[key] = competences.get(key, 0) + value
        earned = [
            r["achievement_id"]
            for r in conn.execute(
                "SELECT achievement_id FROM earned_achievements WHERE conductor_id = ?", (row["id"],)
            )
        ]
        out.append(
            {
                "login": row["login"],
                "brigade": row["brigade"],
                "depot": row["depot"],
                "level": level_of(row["xp"])["name"],
                "xp": row["xp"],
                "runs_completed": len(results),
                "average_score": round(sum(r["score"] for r in results) / len(results)) if results else 0,
                "competences": competences,
                "weak_competences": sorted(k for k, v in competences.items() if v < 0),
                "achievements": earned,
                "streak_days": streak_days(conn, row["id"]),
            }
        )
    return out


def assign(
    conn: sqlite3.Connection,
    login: str,
    content: Content,
    scenario_id: str | None = None,
    trip_id: str | None = None,
) -> dict:
    """Назначить обучение из LMS: проводник увидит уведомление в приложении."""
    conductor = get_conductor(conn, login)
    if conductor is None:
        raise LookupError(f"нет проводника {login!r}")
    if trip_id:
        trip = content.trip(trip_id)
        title, body = f"Назначен рейс: {trip.title}", f"{trip.route}. {trip.summary}"
    elif scenario_id:
        scenario = content.scenario(scenario_id)
        title, body = f"Назначен сценарий: {scenario.title}", scenario.summary
    else:
        raise ValueError("нужен scenario_id или trip_id")
    notify(conn, conductor["id"], "assignment", title, body)
    conn.commit()
    return {"status": "ok", "login": login, "scenario_id": scenario_id, "trip_id": trip_id}
