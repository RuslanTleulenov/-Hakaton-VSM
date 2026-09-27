"""HTTP API тренажёра «Перегон» и раздача статического фронтенда.

Схема OpenAPI доступна на /docs и /openapi.json — это и есть документация
API для интеграции с HR/LMS. Интеграционные методы вынесены в отдельный
раздел `/api/v1/integration/*` и требуют токена клиента.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import service
from .db import connect
from .domain import COMPETENCES, STEPS
from .loader import load_content

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"

app = FastAPI(
    title="Перегон — тренажёр проводника ВСМ",
    version="1.1.0",
    description=(
        "API геймифицированного тренажёра: сценарии и рейсы из нескольких "
        "инцидентов, партии с таймерами, двойные шкалы, профиль, достижения, "
        "рейтинг, челленджи и аналитика компетенций."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # демо-стенд; в проде — список доменов HR/LMS
    allow_methods=["*"],
    allow_headers=["*"],
)

conn = connect()
CONTENT = load_content()


def not_found(exc: LookupError) -> HTTPException:
    return HTTPException(404, str(exc))


def integration_client(x_api_key: str = Header(..., description="Токен интеграции")) -> dict:
    """Интеграционные методы доступны только по токену зарегистрированного клиента."""
    row = conn.execute("SELECT id, name FROM api_clients WHERE token = ?", (x_api_key,)).fetchone()
    if row is None:
        raise HTTPException(401, "неизвестный токен интеграции")
    return dict(row)


class LoginIn(BaseModel):
    login: str = Field(examples=["a.smirnova"])
    display_name: str = Field(examples=["Смирнова А."])
    brigade: str = Field(examples=["Бригада 3"])
    depot: str = Field(examples=["Депо Москва-Пассажирская"])


class StartRunIn(BaseModel):
    login: str
    scenario_id: str | None = Field(default=None, description="Отдельный инцидент")
    trip_id: str | None = Field(default=None, description="Рейс из нескольких инцидентов")
    challenge: bool = Field(default=False, description="Партия идёт в зачёт «Рейса недели»")


class ChooseIn(BaseModel):
    option_id: str | None = Field(default=None, description="null — игрок не успел; ход уходит в timeout")


@app.get("/api/v1/health", tags=["служебное"])
def health() -> dict:
    return {
        "status": "ok",
        "scenarios": len(CONTENT.scenarios),
        "trips": len(CONTENT.trips),
        "achievements": len(CONTENT.achievements),
    }


@app.get("/api/v1/reference", tags=["справочники"])
def reference() -> dict:
    """Компетенции и шаги ролевой модели — для UI и внешних систем."""
    return {"competences": COMPETENCES, "steps": STEPS}


@app.post("/api/v1/conductors", tags=["профиль"])
def upsert_conductor(payload: LoginIn) -> dict:
    """Вход в демо-стенд: профиль заводится по логину, ПДн не собираются."""
    conductor = service.ensure_conductor(
        conn, payload.login, payload.display_name, payload.brigade, payload.depot
    )
    return {"login": conductor["login"], "xp": conductor["xp"]}


@app.get("/api/v1/conductors/{login}", tags=["профиль"])
def get_profile(login: str) -> dict:
    data = service.profile(conn, login, CONTENT.achievements)
    if data is None:
        raise HTTPException(404, f"проводник {login!r} не найден")
    return data


@app.get("/api/v1/scenarios", tags=["сценарии"])
def list_scenarios(login: str | None = None) -> list[dict]:
    order = service.recommended(conn, login, CONTENT) if login else list(CONTENT.scenarios)
    return [
        {
            "id": s.id,
            "title": s.title,
            "summary": s.summary,
            "segment": s.segment,
            "minutes_to_stop": s.minutes_to_stop,
            "car_class": s.car_class,
            "difficulty": s.difficulty,
            "sources": s.sources,
            "nodes": len(s.nodes),
        }
        for s in (CONTENT.scenarios[sid] for sid in order)
    ]


@app.get("/api/v1/trips", tags=["сценарии"])
def list_trips() -> list[dict]:
    """Рейсы: несколько инцидентов подряд с общими шкалами и памятью."""
    return [
        {
            "id": t.id,
            "title": t.title,
            "route": t.route,
            "summary": t.summary,
            "segments": [
                {"id": sid, "title": CONTENT.scenarios[sid].title, "segment": CONTENT.scenarios[sid].segment}
                for sid in t.segments
            ],
            "difficulty": max(CONTENT.scenarios[sid].difficulty for sid in t.segments),
        }
        for t in CONTENT.trips.values()
    ]


@app.post("/api/v1/runs", tags=["партия"])
def start_run(payload: StartRunIn) -> dict:
    week = service.current_week() if payload.challenge else None
    try:
        return service.start_run(
            conn, payload.login, CONTENT, payload.scenario_id, payload.trip_id, week
        )
    except LookupError as exc:
        raise not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/v1/runs/{run_id}/choose", tags=["партия"])
def choose(run_id: str, payload: ChooseIn) -> dict:
    try:
        return service.choose(conn, run_id, CONTENT, payload.option_id)
    except LookupError as exc:
        raise not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/v1/runs/{run_id}/debrief", tags=["партия"])
def debrief(run_id: str) -> dict:
    try:
        return service.debrief(conn, run_id, CONTENT)
    except LookupError as exc:
        raise not_found(exc) from exc


@app.get("/api/v1/leaderboard", tags=["геймификация"])
def leaderboard(scope: str = "company", value: str | None = None) -> list[dict]:
    if scope not in {"company", "brigade", "depot"}:
        raise HTTPException(422, "scope: company | brigade | depot")
    return service.leaderboard(conn, scope, value)


@app.get("/api/v1/challenge", tags=["геймификация"])
def challenge(login: str | None = None) -> dict:
    """Рейс недели: один сценарий для всех бригад, отдельная таблица."""
    return service.challenge(conn, CONTENT, login)


@app.get("/api/v1/conductors/{login}/streak", tags=["геймификация"])
def streak(login: str) -> dict:
    conductor = service.get_conductor(conn, login)
    if conductor is None:
        raise HTTPException(404, f"проводник {login!r} не найден")
    return {
        "streak_days": service.streak_days(conn, conductor["id"]),
        "expiring": service.expiring_points(conn, login),
    }


@app.get("/api/v1/analytics/hotspots", tags=["аналитика"])
def hotspots(limit: int = 10) -> list[dict]:
    """Развилки, на которых чаще всего теряют шкалы, — пробелы в подготовке."""
    return service.hotspots(conn, limit)


@app.get("/api/v1/analytics/trend", tags=["аналитика"])
def trend(login: str, limit: int = 10) -> dict:
    """Динамика компетенций проводника по последним рейсам."""
    try:
        return service.competence_trend(conn, login, limit)
    except LookupError as exc:
        raise not_found(exc) from exc


@app.get("/api/v1/notifications", tags=["геймификация"])
def notifications(login: str) -> list[dict]:
    try:
        return service.notifications(conn, login)
    except LookupError as exc:
        raise not_found(exc) from exc


@app.post("/api/v1/notifications/{notification_id}/read", tags=["геймификация"])
def read_notification(notification_id: int) -> dict:
    service.mark_read(conn, notification_id)
    return {"status": "ok"}


# --- интеграция с HR/LMS ---------------------------------------------------


@app.get("/api/v1/integration/progress", tags=["интеграция"])
def integration_progress(
    depot: str | None = None,
    brigade: str | None = None,
    client: dict = Depends(integration_client),
) -> dict:
    """Выгрузка прогресса для HR/LMS: уровни, баллы, компетенции, достижения.

    Отдаются только учебные показатели — ни одного поля с персональными
    данными: логин это учётная запись в системе обучения, а не сам человек.
    """
    return {
        "client": client["name"],
        "generated_at": service.timestamp(),
        "conductors": service.progress_export(conn, CONTENT.achievements, depot, brigade),
    }


@app.post("/api/v1/integration/assign", tags=["интеграция"])
def integration_assign(payload: StartRunIn, client: dict = Depends(integration_client)) -> dict:
    """Назначение обучения из LMS: проводник получает уведомление о рейсе."""
    try:
        return service.assign(conn, payload.login, CONTENT, payload.scenario_id, payload.trip_id)
    except LookupError as exc:
        raise not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(FRONTEND / "index.html")
