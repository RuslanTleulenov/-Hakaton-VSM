"""Загрузка сценариев и ачивок из YAML с валидацией ссылок между узлами."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .domain import Effects, Node, Option, Scenario, Timeout

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
        start_loyalty=int(raw.get("start_loyalty", 70)),
        start_safety=int(raw.get("start_safety", 80)),
    )
    _validate(scenario)
    return scenario


def _validate(s: Scenario) -> None:
    """Ссылки между узлами проверяются при загрузке, а не в середине партии."""
    s.node(s.start)
    for node in s.nodes.values():
        if node.is_final:
            continue
        if not node.options and not node.timeout:
            raise ValueError(f"{s.id}/{node.id}: не финальный узел без вариантов")
        for opt in node.options:
            s.node(opt.goto)
        if node.timeout:
            s.node(node.timeout.goto)
        if node.timer and not node.timeout:
            raise ValueError(f"{s.id}/{node.id}: есть таймер, но нет ветки timeout")


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
