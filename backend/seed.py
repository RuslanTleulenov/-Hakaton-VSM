"""Наполнение демо-стенда синтетическими данными.

Реальных персональных данных здесь нет и быть не может: логины, имена,
бригады и депо придуманы (152-ФЗ, ограничение кейса). Скрипт проигрывает
партии тем же ядром, что и живой интерфейс, — таблица лидеров получается
из настоящих прохождений, а не из выдуманных чисел.

Запуск:  python backend/seed.py
"""
from __future__ import annotations

import random
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import service
from app.db import connect
from app.loader import Content, load_content

CONDUCTORS = [
    ("a.smirnova", "Смирнова А.", "Бригада 3", "Депо Москва-Пассажирская"),
    ("i.petrov", "Петров И.", "Бригада 3", "Депо Москва-Пассажирская"),
    ("m.kuznetsova", "Кузнецова М.", "Бригада 1", "Депо Санкт-Петербург-Главное"),
    ("d.orlov", "Орлов Д.", "Бригада 1", "Депо Санкт-Петербург-Главное"),
    ("s.voronina", "Воронина С.", "Бригада 7", "Депо Тверь"),
]

# Демо-профиль, который жюри проходит само: его историю не заполняем.
DEMO_LOGIN = "a.smirnova"

# Навык = вероятность выбрать лучший вариант; остаток делится между
# случайным решением и «не успел» — так в демо-данных есть и таймауты.
SKILLS = {
    "i.petrov": 0.55,
    "m.kuznetsova": 0.92,
    "d.orlov": 0.3,
    "s.voronina": 0.72,
}


def play(conn, content: Content, login: str, skill: float, rng: random.Random, **start) -> None:
    """Проиграть партию: чем выше `skill`, тем чаще выбирается лучший вариант."""
    view = service.start_run(conn, login, content, **start)
    while not view["finished"]:
        node = view["node"]
        if not node["options"]:
            break
        scenario = content.scenario(view["scenario"]["id"])
        allowed = {option["id"] for option in node["options"]}      # флаги уже учтены сервером
        choices = [o for o in scenario.node(node["node_id"]).options if o.id in allowed]
        ranked = sorted(choices, key=lambda o: o.effects.safety * 2 + o.effects.loyalty, reverse=True)
        roll = rng.random()
        if roll < skill:
            option_id = ranked[0].id
        elif node["timer"] and roll > 1 - (1 - skill) / 3:
            option_id = None                                        # не успел: сработает timeout
        else:
            option_id = rng.choice(choices).id
        view = service.choose(conn, view["run_id"], content, option_id)


def main() -> None:
    rng = random.Random(20260927)
    conn = connect()
    content = load_content()

    for login, name, brigade, depot in CONDUCTORS:
        service.ensure_conductor(conn, login, name, brigade, depot)

    week = service.current_week()
    challenge_scenario = service.challenge(conn, content)["scenario"]["id"]

    for login, skill in SKILLS.items():
        for scenario_id in content.scenarios:
            play(conn, content, login, skill, rng, scenario_id=scenario_id)
        for trip_id in content.trips:
            play(conn, content, login, skill, rng, trip_id=trip_id)
        # Партия в зачёт «Рейса недели» — чтобы таблица челленджа была не пустой.
        play(conn, content, login, skill, rng, scenario_id=challenge_scenario, challenge_week=week)

    for login, *_ in CONDUCTORS:
        conductor = service.get_conductor(conn, login)
        service.notify(
            conn, conductor["id"], "new_scenario",
            "Новый рейс: «Вечерний рейс 763»",
            "Три инцидента подряд: опьянение, бесхозная вещь и остановка в пути.",
        )
        service.notify(
            conn, conductor["id"], "challenge",
            f"Рейс недели {week}",
            "Один и тот же сценарий для всех бригад — сравнение честное. Бонус 150 очков.",
        )
        service.notify(
            conn, conductor["id"], "expiring_points",
            "Очки челленджа сгорают через неделю простоя",
            "Пройдите любой рейс, чтобы сохранить серию и баллы недели.",
        )
    conn.commit()

    # Токен демо-интеграции: в реальном контуре выдаётся администратором.
    token = "demo-hr-" + secrets.token_hex(8)
    conn.execute("DELETE FROM api_clients WHERE name = 'HR-портал (демо)'")
    conn.execute("INSERT INTO api_clients (name, token) VALUES (?, ?)", ("HR-портал (демо)", token))
    conn.commit()

    print("Проводников:", len(CONDUCTORS), "· сценариев:", len(content.scenarios), "· рейсов:", len(content.trips))
    for row in service.leaderboard(conn):
        print(f'  {row["place"]}. {row["display_name"]:<16} {row["xp"]:>5} опыта  ср. балл {row["avg_score"]}')
    print("\nТокен демо-интеграции (заголовок X-API-Key):", token)


if __name__ == "__main__":
    main()
