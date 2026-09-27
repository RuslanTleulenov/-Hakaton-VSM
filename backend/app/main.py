"""HTTP API тренажёра «Перегон» и раздача статического фронтенда.

Схема OpenAPI доступна на /docs и /openapi.json — это и есть документация
API для интеграции с HR/LMS.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import service
from .db import connect
from .domain import COMPETENCES, STEPS
from .loader import load_achievements, load_scenarios

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"

app = FastAPI(
    title="Перегон — тренажёр проводника ВСМ",
    version="1.0.0",
    description=(
        "API геймифицированного тренажёра: сценарии, партии с таймерами, "
        "двойные шкалы, профиль, достижения, рейтинг и аналитика компетенций."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # демо-стенд; в проде — список доменов HR/LMS
    allow_methods=["*"],
    allow_headers=["*"],
)

conn = connect()
SCENARIOS = load_scenarios()
ACHIEVEMENTS = load_achievements()


def scenario_or_404(scenario_id: str):
    if scenario_id not in SCENARIOS:
        raise HTTPException(404, f"сценарий {scenario_id!r} не найден")
    return SCENARIOS[scenario_id]


class LoginIn(BaseModel):
    login: str = Field(examples=["a.smirnova"])
    display_name: str = Field(examples=["Смирнова А."])
    brigade: str = Field(examples=["Бригада 3"])
    depot: str = Field(examples=["Депо Москва-Пассажирская"])


class StartRunIn(BaseModel):
    login: str
    scenario_id: str


class ChooseIn(BaseModel):
    option_id: str | None = Field(default=None, description="null — игрок не успел; ход уходит в timeout")


@app.get("/api/v1/health", tags=["служебное"])
def health() -> dict:
    return {"status": "ok", "scenarios": len(SCENARIOS), "achievements": len(ACHIEVEMENTS)}


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
    data = service.profile(conn, login, ACHIEVEMENTS)
    if data is None:
        raise HTTPException(404, f"проводник {login!r} не найден")
    return data


@app.get("/api/v1/scenarios", tags=["сценарии"])
def list_scenarios(login: str | None = None) -> list[dict]:
    order = service.recommended(conn, login, SCENARIOS) if login else list(SCENARIOS)
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
        for s in (SCENARIOS[sid] for sid in order)
    ]


@app.post("/api/v1/runs", tags=["партия"])
def start_run(payload: StartRunIn) -> dict:
    scenario = scenario_or_404(payload.scenario_id)
    try:
        return service.start_run(conn, payload.login, scenario)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/v1/runs/{run_id}/choose", tags=["партия"])
def choose(run_id: str, payload: ChooseIn) -> dict:
    try:
        row = conn.execute("SELECT scenario_id FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise HTTPException(404, f"партия {run_id!r} не найдена")
        scenario = scenario_or_404(row["scenario_id"])
        return service.choose(conn, run_id, scenario, payload.option_id, ACHIEVEMENTS)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/v1/runs/{run_id}/debrief", tags=["партия"])
def debrief(run_id: str) -> dict:
    row = conn.execute("SELECT scenario_id FROM runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"партия {run_id!r} не найдена")
    return service.debrief(conn, run_id, scenario_or_404(row["scenario_id"]))


@app.get("/api/v1/leaderboard", tags=["геймификация"])
def leaderboard(scope: str = "company", value: str | None = None) -> list[dict]:
    if scope not in {"company", "brigade", "depot"}:
        raise HTTPException(422, "scope: company | brigade | depot")
    return service.leaderboard(conn, scope, value)


@app.get("/api/v1/analytics/hotspots", tags=["аналитика"])
def hotspots(limit: int = 10) -> list[dict]:
    """Развилки, на которых чаще всего теряют шкалы, — пробелы в подготовке."""
    return service.hotspots(conn, limit)


@app.get("/api/v1/notifications", tags=["геймификация"])
def notifications(login: str) -> list[dict]:
    try:
        return service.notifications(conn, login)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/v1/notifications/{notification_id}/read", tags=["геймификация"])
def read_notification(notification_id: int) -> dict:
    service.mark_read(conn, notification_id)
    return {"status": "ok"}


if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(FRONTEND / "index.html")
