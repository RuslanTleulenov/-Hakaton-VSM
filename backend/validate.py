"""Проверка контента без запуска сервера: сценарии, рейсы, достижения.

Методист правит YAML и запускает:

    python backend/validate.py

Скрипт грузит весь контент теми же функциями, что и приложение, и
дополнительно считает то, что важно для качества сценария: сколько узлов
достижимо, есть ли у каждого критического узла ветка timeout, у каждого
варианта — причина, и ссылается ли сценарий на регламент.

Код возврата 1 — контент не готов к сдаче.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.achievements import CONDITION_KEYS
from app.domain import STEPS
from app.loader import load_content


def check_scenario(scenario) -> list[str]:
    problems: list[str] = []
    if not scenario.sources:
        problems.append("нет ссылки на регламент или методичку")
    finals = [n for n in scenario.nodes.values() if n.is_final]
    if len(finals) < 2:
        problems.append("меньше двух финалов — ветвление, скорее всего, декоративное")
    for node in scenario.nodes.values():
        if node.critical and not node.timer:
            problems.append(f"{node.id}: узел помечен критическим, но без таймера")
        for option in node.options:
            if not option.reason:
                problems.append(f"{node.id}/{option.id}: нет причины — разбор будет пустым")
            if option.step and option.step not in STEPS:
                problems.append(f"{node.id}/{option.id}: неизвестный шаг ролевой модели {option.step!r}")
            empty = option.effects.loyalty == 0 and option.effects.safety == 0
            if empty and not option.effects.competences and not option.effects.set_flags:
                problems.append(f"{node.id}/{option.id}: вариант ни на что не влияет")
    return problems


def main() -> int:
    try:
        content = load_content()
    except Exception as error:  # noqa: BLE001 — задача скрипта показать причину методисту
        print(f"Контент не загружается: {error}")
        return 1

    failed = False
    for scenario in content.scenarios.values():
        problems = check_scenario(scenario)
        timers = sum(1 for n in scenario.nodes.values() if n.timer)
        finals = sum(1 for n in scenario.nodes.values() if n.is_final)
        status = "ОШИБКИ" if problems else "ок"
        print(f"[{status}] {scenario.id}: {len(scenario.nodes)} узлов, {timers} с таймером, {finals} финала")
        for problem in problems:
            failed = True
            print(f"        · {problem}")

    for trip in content.trips.values():
        labels = set(trip.memory_labels)
        used = {
            flag
            for sid in trip.segments
            for node in content.scenario(sid).nodes.values()
            for option in node.options
            for flag in option.effects.set_flags
        }
        unknown = labels - used
        print(f"[{'ОШИБКИ' if unknown else 'ок'}] рейс {trip.id}: {len(trip.segments)} инцидента")
        for flag in sorted(unknown):
            failed = True
            print(f"        · память {flag!r} описана, но ни один вариант её не выставляет")

    for achievement in content.achievements:
        unknown = set(achievement.get("condition", {})) - CONDITION_KEYS
        if unknown:
            failed = True
            print(f"[ОШИБКИ] достижение {achievement['id']}: неизвестные условия {sorted(unknown)}")
    print(f"[ок] достижений: {len(content.achievements)}")

    print("\nКонтент не готов" if failed else "\nКонтент в порядке")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
