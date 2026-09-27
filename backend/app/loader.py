"""Загрузка сценариев и ачивок из YAML с валидацией ссылок между узлами."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .domain import MOODS, Branch, Character, Effects, Node, Option, Scenario, Timeout, Trip

CONTENT = Path(__file__).resolve().parents[2] / "content"


def _option(raw: dict[str, Any]) -> Option:
    return Option(
        id=raw["id"],
        text=raw["text"],
        goto=raw["goto"],
        reason=raw.get("reason", ""),
        step=raw.get("step"),
        effects=Effects.parse(raw.get("effects")),
        requires=list(raw.get("requires", [])),
        forbidden=list(raw.get("forbidden", [])),
        better=raw.get("better"),
        goto_if=[Branch(flag=b["flag"], goto=b["goto"]) for b in raw.get("goto_if", [])],
    )


def _node(node_id: str, raw: dict[str, Any]) -> Node:
    timeout = None
    if raw.get("timeout"):
        t = raw["timeout"]
        timeout = Timeout(goto=t["goto"], reason=t.get("reason", ""), effects=Effects.parse(t.get("effects")))
    return Node(
        id=node_id,
        text=raw["text"],
        speaker=raw.get("speaker", "narrator"),
        timer=raw.get("timer"),
        critical=bool(raw.get("critical", False)),
        options=[_option(o) for o in raw.get("options", [])],
        timeout=timeout,
        ending=raw.get("ending"),
        scene=raw.get("scene"),
        character=raw.get("character"),
        mood=raw.get("mood", "calm"),
    )


def parse_scenario(raw: dict[str, Any]) -> Scenario:
    nodes = {nid: _node(nid, n) for nid, n in raw["nodes"].items()}
    scenario = Scenario(
        id=raw["id"],
        title=raw["title"],
        summary=raw["summary"],
        segment=raw["segment"],
        minutes_to_stop=int(raw["minutes_to_stop"]),
        car_class=raw.get("car_class", "комфорт"),
        difficulty=int(raw.get("difficulty", 1)),
        sources=list(raw.get("sources", [])),
        start=raw["start"],
        nodes=nodes,
        scene=raw.get("scene"),
        characters={
            cid: Character(id=cid, name=c["name"], sprite=c.get("sprite", cid), role=c.get("role", ""))
            for cid, c in raw.get("characters", {}).items()
        },
        start_loyalty=int(raw.get("start_loyalty", 70)),
        start_safety=int(raw.get("start_safety", 80)),
    )
    _validate(scenario)
    return scenario


def _validate(s: Scenario) -> None:
    """Ссылки между узлами проверяются при загрузке, а не в середине партии."""
    s.node(s.start)
    reachable = {s.start}
    for node in s.nodes.values():
        if node.is_final:
            continue
        if not node.options and not node.timeout:
            raise ValueError(f"{s.id}/{node.id}: не финальный узел без вариантов")
        for opt in node.options:
            s.node(opt.goto)
            reachable.add(opt.goto)
            for branch in opt.goto_if:
                s.node(branch.goto)
                reachable.add(branch.goto)
        if node.timeout:
            s.node(node.timeout.goto)
            reachable.add(node.timeout.goto)
        if node.timer and not node.timeout:
            raise ValueError(f"{s.id}/{node.id}: есть таймер, но нет ветки timeout")
    for node in s.nodes.values():
        if node.character and node.character not in s.characters:
            raise ValueError(f"{s.id}/{node.id}: персонаж {node.character!r} не описан в characters")
        if node.mood not in MOODS:
            raise ValueError(f"{s.id}/{node.id}: неизвестное настроение {node.mood!r}")
    unreachable = set(s.nodes) - reachable
    if unreachable:
        raise ValueError(f"{s.id}: недостижимые узлы {sorted(unreachable)}")
    if not any(node.is_final for node in s.nodes.values()):
        raise ValueError(f"{s.id}: нет ни одного финального узла")


def load_scenarios(path: Path | None = None) -> dict[str, Scenario]:
    folder = path or CONTENT / "scenarios"
    out: dict[str, Scenario] = {}
    for f in sorted(folder.glob("*.yaml")):
        s = parse_scenario(yaml.safe_load(f.read_text(encoding="utf-8")))
        if s.id in out:
            raise ValueError(f"дубль сценария {s.id}")
        out[s.id] = s
    return out


def load_achievements(path: Path | None = None) -> list[dict[str, Any]]:
    f = path or CONTENT / "achievements.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8"))["achievements"]


def parse_trip(raw: dict[str, Any]) -> Trip:
    return Trip(
        id=raw["id"],
        title=raw["title"],
        summary=raw["summary"],
        route=raw["route"],
        segments=list(raw["segments"]),
        memory_labels=dict(raw.get("memory_labels", {})),
        start_loyalty=int(raw.get("start_loyalty", 70)),
        start_safety=int(raw.get("start_safety", 85)),
    )


def load_trips(scenarios: dict[str, Scenario], path: Path | None = None) -> dict[str, Trip]:
    """Рейсы из нескольких инцидентов. Состав рейса проверяется сразу."""
    folder = path or CONTENT / "trips"
    out: dict[str, Trip] = {}
    if not folder.exists():
        return out
    for f in sorted(folder.glob("*.yaml")):
        trip = parse_trip(yaml.safe_load(f.read_text(encoding="utf-8")))
        if len(trip.segments) < 2:
            raise ValueError(f"рейс {trip.id}: нужно минимум два инцидента")
        for scenario_id in trip.segments:
            if scenario_id not in scenarios:
                raise ValueError(f"рейс {trip.id}: нет сценария {scenario_id!r}")
        out[trip.id] = trip
    return out


@dataclass
class Content:
    """Весь контент тренажёра, загруженный и проверенный один раз при старте."""

    scenarios: dict[str, Scenario] = field(default_factory=dict)
    trips: dict[str, Trip] = field(default_factory=dict)
    achievements: list[dict[str, Any]] = field(default_factory=list)

    def scenario(self, scenario_id: str) -> Scenario:
        try:
            return self.scenarios[scenario_id]
        except KeyError:
            raise LookupError(f"сценарий {scenario_id!r} не найден") from None

    def trip(self, trip_id: str) -> Trip:
        try:
            return self.trips[trip_id]
        except KeyError:
            raise LookupError(f"рейс {trip_id!r} не найден") from None


def load_content(root: Path | None = None) -> Content:
    base = root or CONTENT
    scenarios = load_scenarios(base / "scenarios")
    return Content(
        scenarios=scenarios,
        trips=load_trips(scenarios, base / "trips"),
        achievements=load_achievements(base / "achievements.yaml"),
    )
