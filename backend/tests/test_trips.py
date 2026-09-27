"""Тесты рейса из нескольких инцидентов: общие шкалы, память, альтернативы."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import engine
from app.loader import load_content

CONTENT = load_content()


def play(scenario, state, option_ids, seconds=3):
    for option_id in option_ids:
        engine.choose(scenario, state, option_id, seconds)


def test_trips_reference_existing_scenarios():
    assert set(CONTENT.trips) == {"day-751", "evening-763"}
    for trip in CONTENT.trips.values():
        assert len(trip.segments) >= 2
        assert all(sid in CONTENT.scenarios for sid in trip.segments)
        assert trip.memory_labels, f"{trip.id}: у рейса нет расшифровки памяти"


def test_scales_and_memory_carry_over_between_incidents():
    trip = CONTENT.trip("day-751")
    first = CONTENT.scenario(trip.segments[0])
    state = engine.start_trip(trip, first)

    play(first, state, ["both", "upgrade", "thanks"])
    assert state.finished and state.queue == ["lost-child", "medical"]
    assert "goodwill_car" in state.flags

    loyalty_after_first = state.loyalty
    second = CONTENT.scenario(state.queue[0])
    engine.continue_trip(state, second)

    assert not state.finished
    assert state.loyalty == loyalty_after_first      # шкалы не обнуляются
    assert "goodwill_car" in state.flags             # память едет дальше
    assert state.node_id == second.start


def test_memory_unlocks_option_in_later_incident():
    """Салон, с которым проводник нашёл общий язык, помогает в медицинском инциденте."""
    medical = CONTENT.scenario("medical")

    cold = engine.start(medical)
    play(medical, cold, ["ask", "radio", "empathy"])
    assert "neighbour_help" not in {o.id for o in engine.available_options(medical, cold)}

    warm = engine.start(medical)
    warm.flags.add("goodwill_car")
    play(medical, warm, ["ask", "radio", "empathy"])
    assert "neighbour_help" in {o.id for o in engine.available_options(medical, warm)}


def test_memory_changes_where_the_same_choice_leads():
    """Тот же ход ведёт в другой узел, если вагон помнит публичный спор."""
    medical = CONTENT.scenario("medical")

    calm = engine.start(medical)
    play(medical, calm, ["ask", "radio", "empathy", "screen"])
    assert calm.finished

    tense = engine.start(medical)
    tense.flags.add("car_tense")
    play(medical, tense, ["ask", "radio", "empathy", "screen"])
    assert tense.node_id == "filmed" and not tense.finished


def test_ptb_memory_speeds_up_security_in_evening_trip():
    bag = CONTENT.scenario("unattended-bag")

    unknown = engine.start(bag)
    play(bag, unknown, ["thanks_and_check", "radio_ptb"])
    assert unknown.node_id == "waiting"

    known = engine.start(bag)
    known.flags.add("ptb_known")
    play(bag, known, ["thanks_and_check", "radio_ptb"])
    assert known.node_id == "fast_ptb"


def test_debrief_offers_alternative_only_when_it_was_clearly_better():
    medical = CONTENT.scenario("medical")
    weak = engine.start(medical)
    event = engine.choose(medical, weak, "pills", seconds=3)
    assert event.alternative is not None
    assert event.alternative.option_id == "ask"

    strong = engine.start(medical)
    best = engine.choose(medical, strong, "ask", seconds=3)
    assert best.alternative is None          # лучше уже некуда — молчим


def test_trip_score_averages_endings_of_all_incidents():
    trip = CONTENT.trip("day-751")
    first = CONTENT.scenario(trip.segments[0])
    state = engine.start_trip(trip, first)
    play(first, state, ["both", "upgrade", "thanks"])
    engine.continue_trip(state, CONTENT.scenario("lost-child"))
    play(CONTENT.scenario("lost-child"), state, ["child_first", "report_child", "distract", "calm_mother"])

    result = engine.score(CONTENT.scenario("lost-child"), state)
    assert result["trip_id"] == "day-751"
    assert [s["scenario_id"] for s in result["segments"]] == ["double-seat", "lost-child"]
    assert result["score"] > 80


def test_continue_trip_rejects_wrong_scenario():
    trip = CONTENT.trip("evening-763")
    first = CONTENT.scenario(trip.segments[0])
    state = engine.start_trip(trip, first)
    with pytest.raises(ValueError):
        engine.continue_trip(state, CONTENT.scenario("medical"))
