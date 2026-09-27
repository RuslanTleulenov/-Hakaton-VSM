"""Наполнение демо-стенда синтетическими данными.

Реальных персональных данных здесь нет и быть не может: логины, имена,
бригады и депо придуманы (152-ФЗ, ограничение кейса). Скрипт проигрывает
партии тем же ядром, что и живой интерфейс, — таблица лидеров получается
из настоящих прохождений, а не из выдуманных чисел.

Запуск:  python backend/seed.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import engine, service
from app.db import connect, dumps
from app.loader import load_achievements, load_scenarios

CONDUCTORS = [
    ("a.smirnova", "Смирнова А.", "Бригада 3", "Депо Москва-Пассажирская"),
    ("i.petrov", "Петров И.", "Бригада 3", "Депо Москва-Пассажирская"),
    ("m.kuznetsova", "Кузнецова М.", "Бригада 1", "Депо Санкт-Петербург-Главное"),
    ("d.orlov", "Орлов Д.", "Бригада 1", "Депо Санкт-Петербург-Главное"),
    ("s.voronina", "Воронина С.", "Бригада 7", "Депо Тверь"),
]


def play(conn, scenarios, catalog, login: str, scenario_id: str, skill: float, rng: random.Random) -> None:
    """Проиграть партию: чем выше `skill`, тем чаще выбирается лучший вариант."""
    scenario = scenarios[scenario_id]
    view = service.start_run(conn, login, scenario)
    while not view["finished"]:
        options = view["node"]["options"]
        if not options:
            break
        # «Лучший» вариант оцениваем по эффекту на шкалы — это делает ядро,
        # поэтому здесь просто выбираем между первым (обычно верным) и случайным.
        node = scenario.node(view["node"]["node_id"])
        allowed = {o["id"] for o in options}          # флаги уже учтены сервером
        choices = [o for o in node.options if o.id in allowed]
        ranked = sorted(choices, key=lambda o: o.effects.safety * 2 + o.effects.loyalty, reverse=True)
        choice = ranked[0] if rng.random() < skill else rng.choice(choices)
        view = service.choose(conn, view["run_id"], scenario, choice.id, catalog)


def main() -> None:
    rng = random.Random(20260927)
    conn = connect()
    scenarios = load_scenarios()
    catalog = load_achievements()

    for login, name, brigade, depot in CONDUCTORS:
        service.ensure_conductor(conn, login, name, brigade, depot)

    skills = {"a.smirnova": 0.8, "i.petrov": 0.55, "m.kuznetsova": 0.9, "d.orlov": 0.4, "s.voronina": 0.7}
    for login, skill in skills.items():
        if login == "a.smirnova":
            continue  # демо-профиль оставляем пустым: жюри проходит рейсы само
        for scenario_id in scenarios:
            for _ in range(2):
                play(conn, scenarios, catalog, login, scenario_id, skill, rng)

    # Уведомления: новый сценарий, челлендж недели и сгорающие баллы.
    for login, *_ in CONDUCTORS:
        conductor = service.get_conductor(conn, login)
        service.notify(
            conn, conductor["id"], "new_scenario",
            "Новый рейс: «Пассажир с признаками опьянения»",
            "Добавлен сценарий на перегон Тверь — Санкт-Петербург, сложность ★★★.",
        )
        service.notify(
            conn, conductor["id"], "challenge",
            "Рейс недели: «Пассажиру стало плохо»",
            "Один и тот же сценарий для всех бригад до воскресенья — сравнение честное.",
        )
        service.notify(
            conn, conductor["id"], "expiring_points",
            "Сгорают 120 очков челленджа",
            "Очки прошлой недели сгорят в понедельник — пройдите один рейс, чтобы сохранить серию.",
        )
    conn.commit()

    print("Готово. Проводников:", len(CONDUCTORS))
    for row in service.leaderboard(conn):
        print(f'  {row["place"]}. {row["display_name"]:<16} {row["xp"]:>5} опыта  ср. балл {row["avg_score"]}')


if __name__ == "__main__":
    main()
