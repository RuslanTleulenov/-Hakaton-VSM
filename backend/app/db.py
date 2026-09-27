"""Хранилище на SQLite: проводники, партии, ходы, достижения, уведомления.

SQLite выбран осознанно: нужен один файл и нулевая настройка при проверке
жюри. Слой узкий и синхронный, при переезде на PostgreSQL меняется только
он — API и ядро его не видят.

Персональных данных нет: профиль — это логин, отображаемое имя, бригада
и депо, всё синтетическое (152-ФЗ, ограничение кейса).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "trainer.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS conductors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    brigade TEXT NOT NULL,
    depot TEXT NOT NULL,
    xp INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    conductor_id INTEGER NOT NULL REFERENCES conductors(id),
    scenario_id TEXT NOT NULL,        -- текущий инцидент (для рейса — последний начатый)
    trip_id TEXT,                     -- заполнен, если партия это рейс из нескольких инцидентов
    challenge_week TEXT,              -- ISO-неделя, если партия сыграна в «рейсе недели»
    state TEXT NOT NULL,              -- сериализованный RunState
    node_shown_at TEXT,               -- когда сервер показал текущий узел
    finished INTEGER NOT NULL DEFAULT 0,
    result TEXT,                      -- итог партии (JSON) после финала
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS run_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(id),
    position INTEGER NOT NULL,
    payload TEXT NOT NULL             -- Event в JSON: узел, выбор, дельты, причины
);

CREATE TABLE IF NOT EXISTS earned_achievements (
    conductor_id INTEGER NOT NULL REFERENCES conductors(id),
    achievement_id TEXT NOT NULL,
    run_id TEXT REFERENCES runs(id),
    earned_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (conductor_id, achievement_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conductor_id INTEGER NOT NULL REFERENCES conductors(id),
    kind TEXT NOT NULL,               -- new_scenario | challenge | expiring_points | achievement
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS api_clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,               -- «HR-портал», «LMS»
    token TEXT NOT NULL UNIQUE,       -- выдаётся администратором стенда
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_runs_conductor ON runs(conductor_id);
CREATE INDEX IF NOT EXISTS idx_events_run ON run_events(run_id);
"""

# Колонки, добавленные после первого релиза схемы: база разработчика и стенда
# обновляется на месте, без пересоздания.
MIGRATIONS = {
    "runs": {
        "trip_id": "ALTER TABLE runs ADD COLUMN trip_id TEXT",
        "challenge_week": "ALTER TABLE runs ADD COLUMN challenge_week TEXT",
    },
}


def _migrate(conn: sqlite3.Connection) -> None:
    for table, columns in MIGRATIONS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for column, statement in columns.items():
            if column not in existing:
                conn.execute(statement)
    conn.commit()


def connect(path: Path | None = None) -> sqlite3.Connection:
    target = Path(path or DB_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(value: str) -> Any:
    return json.loads(value)
