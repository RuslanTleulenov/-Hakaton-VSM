"""Тесты ядра: ветвление, таймеры, шкалы, ролевая модель, итог."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import engine
from app.loader import load_achievements, load_scenarios, parse_scenario
from app.achievements import newly_earned

SCENARIOS = load_scenarios()


def test_all_scenarios_load_and_validate():
    assert set(SCENARIOS) == {
        "medical",
        "double-seat",
        "intoxicated",
        "unattended-bag",
        "lost-child",
        "delay-panic",
    }
    for scenario in SCENARIOS.values():
        assert scenario.sources, f"{scenario.id}: нет ссылки на регламент"
        for node in scenario.nodes.values():
            assert node.is_final or node.options or node.timeout


def test_broken_goto_is_rejected_on_load():
    raw = {
        "id": "x", "title": "x", "summary": "x", "segment": "x", "minutes_to_stop": 1,
        "start": "a",
        "nodes": {"a": {"text": "t", "options": [{"id": "o", "text": "t", "goto": "nowhere", "reason": "r"}]}},
    }
    with pytest.raises(ValueError):
        parse_scenario(raw)


def test_timer_without_timeout_branch_is_rejected():
    raw = {
        "id": "x", "title": "x", "summary": "x", "segment": "x", "minutes_to_stop": 1,
        "start": "a",
        "nodes": {
            "a": {"text": "t", "timer": 10, "options": [{"id": "o", "text": "t", "goto": "b", "reason": "r"}]},
            "b": {"text": "end", "ending": "good"},
        },
    }
    with pytest.raises(ValueError):
        parse_scenario(raw)


def test_good_line_in_medical_ends_well():
    """Сильная линия: оценить состояние → вызвать медиков → эмпатия → закрыть контакт."""
    scenario = SCENARIOS["medical"]
    state = engine.start(scenario)
    for option_id in ["ask", "radio", "empathy", "breathing"]:
        engine.choose(scenario, state, option_id, seconds=5)
    assert state.finished
    result = engine.score(scenario, state)
    assert state.ending == "good"
    assert result["safety"] >= 90
    assert result["grade"] == "Отлично"


def test_personal_medicine_costs_safety():
    """Личное лекарство — прямой удар по безопасности, а не мелкая ошибка."""
    scenario = SCENARIOS["medical"]
    state = engine.start(scenario)
    event = engine.choose(scenario, state, "pills", seconds=4)
    assert event.safety_delta <= -20
    assert state.competences["safety"] < 0
    assert event.better


def test_timeout_advances_the_story_and_hurts_composure():
    scenario = SCENARIOS["medical"]
    state = engine.start(scenario)
    event = engine.choose(scenario, state, "ask", seconds=999)   # время вышло
    assert event.timed_out
    assert event.option_id is None
    assert state.node_id == "delayed_start"
    assert state.competences["composure"] == -2


def test_role_model_order_changes_loyalty():
    """Одна и та же реплика-правило стоит по-разному до и после признания."""
    scenario = SCENARIOS["intoxicated"]

    cold = engine.start(scenario)
    event_cold = engine.choose(scenario, cold, "hard_refuse", seconds=3)

    warm = engine.start(scenario)
    engine.choose(scenario, warm, "soft_refuse", seconds=3)       # solution
    engine.choose(scenario, warm, "radio_chief", seconds=3)
    event_warm = engine.choose(scenario, warm, "stop_smoking", seconds=3)  # rule после шагов

    assert event_cold.loyalty_delta < event_warm.loyalty_delta
    assert any("ролевая модель" in r for r in event_cold.reasons)


def test_flags_gate_options():
    """Повышение класса без доплаты доступно только после проверки билетов."""
    scenario = SCENARIOS["double-seat"]
    state = engine.start(scenario)
    engine.choose(scenario, state, "side", seconds=3)             # билеты не проверены
    ids = {o.id for o in engine.available_options(scenario, state)}
    assert "upgrade" not in ids

    state2 = engine.start(scenario)
    engine.choose(scenario, state2, "both", seconds=3)            # билеты проверены
    ids2 = {o.id for o in engine.available_options(scenario, state2)}
    assert "upgrade" in ids2


def test_fast_critical_decision_builds_composure():
    scenario = SCENARIOS["medical"]
    fast = engine.start(scenario)
    engine.choose(scenario, fast, "ask", seconds=2)
    slow = engine.start(scenario)
    engine.choose(scenario, slow, "ask", seconds=19)
    assert fast.competences["composure"] > slow.competences["composure"]


def test_unknown_option_is_rejected():
    scenario = SCENARIOS["medical"]
    state = engine.start(scenario)
    with pytest.raises(ValueError):
        engine.choose(scenario, state, "no-such-option", seconds=1)


def test_achievements_are_awarded_from_result():
    catalog = load_achievements()
    scenario = SCENARIOS["medical"]
    state = engine.start(scenario)
    for option_id in ["ask", "radio", "empathy", "breathing"]:
        engine.choose(scenario, state, option_id, seconds=3)
    result = engine.score(scenario, state)
    earned = {a["id"] for a in newly_earned(catalog, set(), result, runs_completed=1)}
    assert "first-run" in earned
    assert "cold-head" in earned
