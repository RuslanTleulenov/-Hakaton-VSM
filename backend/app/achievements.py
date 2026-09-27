"""Проверка достижений.

Условия описаны в `content/achievements.yaml` декларативно: методист
добавляет ачивку, не трогая код. Поддерживаемые поля условия —
`min_score`, `min_loyalty`, `min_safety`, `max_timeouts`, `ending`,
`min_competence` и `runs_completed`; неизвестное поле — ошибка загрузки,
а не молчаливое «условие всегда истинно».
"""
from __future__ import annotations

from typing import Any

CONDITION_KEYS = {
    "min_score",
    "min_loyalty",
    "min_safety",
    "max_timeouts",
    "ending",
    "min_competence",
    "runs_completed",
}


def check(condition: dict[str, Any], result: dict[str, Any], runs_completed: int) -> bool:
    unknown = set(condition) - CONDITION_KEYS
    if unknown:
        raise ValueError(f"неизвестное условие достижения: {sorted(unknown)}")

    if "min_score" in condition and result["score"] < condition["min_score"]:
        return False
    if "min_loyalty" in condition and result["loyalty"] < condition["min_loyalty"]:
        return False
    if "min_safety" in condition and result["safety"] < condition["min_safety"]:
        return False
    if "max_timeouts" in condition and result["timeouts"] > condition["max_timeouts"]:
        return False
    if "ending" in condition and result["ending"] != condition["ending"]:
        return False
    if "runs_completed" in condition and runs_completed < condition["runs_completed"]:
        return False
    for key, value in condition.get("min_competence", {}).items():
        if result["competences"].get(key, 0) < value:
            return False
    return True


def newly_earned(
    catalog: list[dict[str, Any]],
    already: set[str],
    result: dict[str, Any],
    runs_completed: int,
) -> list[dict[str, Any]]:
    """Ачивки, заработанные именно этой партией."""
    return [
        a
        for a in catalog
        if a["id"] not in already and check(a.get("condition", {}), result, runs_completed)
    ]
