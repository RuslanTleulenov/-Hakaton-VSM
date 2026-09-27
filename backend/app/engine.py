"""Ядро тренажёра: исполнение сценария, шкалы, таймеры, итог партии.

Ядро детерминированное и не знает ни про HTTP, ни про БД: одни и те же
решения в одни и те же моменты времени всегда дают один результат — иначе
таблицу лидеров нельзя считать честной.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .domain import COMPETENCES, Effects, Node, Option, Scenario, Trip

# Порядок шагов ролевой модели из методички «Примеры ситуаций взаимодействия
# поездного персонала с пассажирами»: признать → правило → решение → заверить.
# Проводник может сказать всё правильное, но не в том порядке — и пассажир
# услышит отписку. Поэтому порядок шагов считается отдельно от самих реплик.
SEQUENCE_RULES = [
    {
        "step": "rule",
        "after": [None, "action"],
        "loyalty": -4,
        "competences": {},
        "reason": "Правило без признания ситуации звучит казённо — ролевая модель нарушена",
    },
    {
        "step": "solution",
        "after": ["acknowledge", "rule"],
        "loyalty": 3,
        "competences": {"service": 1},
        "reason": "Решение предложено после признания ситуации — ролевая модель соблюдена",
    },
    {
        "step": "assure",
        "after": ["solution"],
        "loyalty": 2,
        "competences": {"service": 1},
        "reason": "Пассажира заверили после решения — контакт закрыт",
    },
]

# Решение в первой половине таймера считается принятым вовремя.
FAST_DECISION_SHARE = 0.5


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


@dataclass
class Alternative:
    """Ветка, которую игрок не выбрал, — «что было бы, если».

    Показывается в разборе только там, где альтернатива была заметно лучше:
    обучающая обратная связь, а не перечисление всех кнопок.
    """

    option_id: str
    text: str
    reason: str
    loyalty: int
    safety: int


@dataclass
class Event:
    """Один ход партии — основа разбора и аналитики."""

    node_id: str
    node_text: str
    option_id: str | None          # None — время вышло
    option_text: str
    step: str | None
    seconds: float                 # сколько думал
    timer: int | None
    timed_out: bool
    loyalty_delta: int
    safety_delta: int
    competence_deltas: dict[str, int]
    reasons: list[str]
    better: str | None
    scenario_id: str = ""
    alternative: Alternative | None = None


@dataclass
class RunState:
    """Состояние партии. Сериализуется в БД, поэтому без ссылок на сценарий.

    Партия — это либо один инцидент, либо рейс из нескольких: тогда
    `queue` хранит оставшиеся сценарии, а флаги и шкалы переходят дальше.
    """

    scenario_id: str
    node_id: str
    loyalty: int
    safety: int
    competences: dict[str, int] = field(default_factory=lambda: {k: 0 for k in COMPETENCES})
    flags: set[str] = field(default_factory=set)
    last_step: str | None = None
    events: list[Event] = field(default_factory=list)
    finished: bool = False
    ending: str | None = None
    trip_id: str | None = None
    queue: list[str] = field(default_factory=list)      # ещё не сыгранные инциденты рейса
    segments: list[dict[str, Any]] = field(default_factory=list)   # исход каждого инцидента


def start(scenario: Scenario) -> RunState:
    return RunState(
        scenario_id=scenario.id,
        node_id=scenario.start,
        loyalty=scenario.start_loyalty,
        safety=scenario.start_safety,
    )


def start_trip(trip: Trip, first: Scenario) -> RunState:
    """Начать рейс: шкалы общие на всю смену, очередь инцидентов — из маршрута."""
    return RunState(
        scenario_id=first.id,
        node_id=first.start,
        loyalty=trip.start_loyalty,
        safety=trip.start_safety,
        trip_id=trip.id,
        queue=list(trip.segments[1:]),
    )


def continue_trip(state: RunState, nxt: Scenario) -> None:
    """Перейти к следующему инциденту рейса, сохранив шкалы и память.

    Память — это те же флаги: пассажир, которому отказали в первом вагоне,
    узнаётся в третьем, потому что флаг о нём никуда не делся.
    """
    if not state.queue or state.queue[0] != nxt.id:
        raise ValueError(f"инцидент {nxt.id!r} не следующий в рейсе")
    state.segments.append({"scenario_id": state.scenario_id, "ending": state.ending})
    state.queue.pop(0)
    state.scenario_id = nxt.id
    state.node_id = nxt.start
    state.finished = False
    state.ending = None
    state.last_step = None


def available_options(scenario: Scenario, state: RunState) -> list[Option]:
    """Варианты с учётом флагов: мягкие пути закрываются по ходу инцидента."""
    node = scenario.node(state.node_id)
    return [o for o in node.options if o.available(state.flags)]


def _apply(state: RunState, eff: Effects, reasons: list[str], reason: str) -> tuple[int, int, dict[str, int]]:
    before_loyalty, before_safety = state.loyalty, state.safety
    state.loyalty = clamp(state.loyalty + eff.loyalty)
    state.safety = clamp(state.safety + eff.safety)
    deltas: dict[str, int] = {}
    for key, value in eff.competences.items():
        state.competences[key] = state.competences.get(key, 0) + value
        deltas[key] = value
    state.flags |= set(eff.set_flags)
    state.flags -= set(eff.clear_flags)
    if reason:
        reasons.append(reason)
    return state.loyalty - before_loyalty, state.safety - before_safety, deltas


def _sequence_rule(step: str | None, last_step: str | None) -> tuple[Effects, str] | None:
    for rule in SEQUENCE_RULES:
        if rule["step"] == step and last_step in rule["after"]:
            return (
                Effects(loyalty=rule["loyalty"], competences=dict(rule["competences"])),
                rule["reason"],
            )
    return None


def _weight(option: Option) -> int:
    """Цена варианта глазами тренажёра: безопасность весит вдвое."""
    return option.effects.safety * 2 + option.effects.loyalty


# Насколько альтернатива должна быть лучше, чтобы о ней стоило говорить в разборе.
ALTERNATIVE_GAP = 6

# Псевдо-вариант «игрок не ответил»: с ним сравнивается любой пропущенный таймер.
_NO_CHOICE = Option(id="", text="", goto="", reason="")


def _alternative(options: list[Option], chosen: Option) -> Alternative | None:
    others = [o for o in options if o.id != chosen.id]
    if not others:
        return None
    best = max(others, key=_weight)
    if _weight(best) - _weight(chosen) < ALTERNATIVE_GAP:
        return None
    return Alternative(
        option_id=best.id,
        text=best.text,
        reason=best.reason,
        loyalty=best.effects.loyalty,
        safety=best.effects.safety,
    )


def _merge(into: dict[str, int], extra: dict[str, int]) -> None:
    for key, value in extra.items():
        into[key] = into.get(key, 0) + value


def choose(scenario: Scenario, state: RunState, option_id: str | None, seconds: float) -> Event:
    """Применить решение проводника.

    `seconds` — время с момента показа узла, его считает сервер: клиент не
    может «остановить» таймер. Если время вышло или пришёл `option_id=None`,
    срабатывает ветка timeout — бездействие тоже развивает ситуацию.
    """
    if state.finished:
        raise ValueError("партия уже завершена")
    node = scenario.node(state.node_id)
    expired = node.timer is not None and seconds > node.timer
    if option_id is None or expired:
        return _timeout(scenario, state, node, seconds)

    available_at_start = available_options(scenario, state)
    option = next((o for o in available_at_start if o.id == option_id), None)
    if option is None:
        raise ValueError(f"вариант {option_id!r} недоступен в узле {node.id}")

    reasons: list[str] = []
    loyalty_delta, safety_delta, competence_deltas = _apply(state, option.effects, reasons, option.reason)

    sequence = _sequence_rule(option.step, state.last_step)
    if sequence:
        effects, reason = sequence
        extra_loyalty, extra_safety, extra_competences = _apply(state, effects, reasons, reason)
        loyalty_delta += extra_loyalty
        safety_delta += extra_safety
        _merge(competence_deltas, extra_competences)

    if node.critical and node.timer:
        fast = seconds <= node.timer * FAST_DECISION_SHARE
        effects = Effects(competences={"composure": 2 if fast else -1})
        reason = (
            "Критическое решение принято быстро — хладнокровие"
            if fast
            else "Решение верное, но принято на исходе таймера — в рейсе это дорого"
        )
        _, _, extra_competences = _apply(state, effects, reasons, reason)
        _merge(competence_deltas, extra_competences)

    if option.step:
        state.last_step = option.step

    event = Event(
        node_id=node.id,
        node_text=node.text,
        option_id=option.id,
        option_text=option.text,
        step=option.step,
        seconds=round(seconds, 1),
        timer=node.timer,
        timed_out=False,
        loyalty_delta=loyalty_delta,
        safety_delta=safety_delta,
        competence_deltas=competence_deltas,
        reasons=reasons,
        better=option.better,
        scenario_id=scenario.id,
        alternative=_alternative(available_at_start, option),
    )
    state.events.append(event)
    _advance(scenario, state, option.target(state.flags))
    return event


def _timeout(scenario: Scenario, state: RunState, node: Node, seconds: float) -> Event:
    if node.timeout is None:
        raise ValueError(f"узел {node.id}: время вышло, но ветка timeout не описана")
    reasons: list[str] = []
    loyalty_delta, safety_delta, competence_deltas = _apply(state, node.timeout.effects, reasons, node.timeout.reason)
    _, _, extra = _apply(state, Effects(competences={"composure": -2}), reasons, "Решение не принято вовремя")
    _merge(competence_deltas, extra)
    event = Event(
        node_id=node.id,
        node_text=node.text,
        option_id=None,
        option_text="Время вышло — ситуация развивалась сама",
        step=None,
        seconds=round(seconds, 1),
        timer=node.timer,
        timed_out=True,
        loyalty_delta=loyalty_delta,
        safety_delta=safety_delta,
        competence_deltas=competence_deltas,
        reasons=reasons,
        better="Бездействие — тоже решение: лучше быстрый неидеальный шаг, чем истёкший таймер",
        scenario_id=scenario.id,
        alternative=_alternative(available_options(scenario, state), _NO_CHOICE),
    )
    state.events.append(event)
    _advance(scenario, state, node.timeout.goto)
    return event


def _advance(scenario: Scenario, state: RunState, node_id: str) -> None:
    state.node_id = node_id
    node = scenario.node(node_id)
    if node.is_final:
        state.finished = True
        state.ending = node.ending


# --- итог партии -----------------------------------------------------------

GRADES = [(85, "Отлично"), (70, "Хорошо"), (50, "Удовлетворительно"), (0, "Требует отработки")]


def score(scenario: Scenario, state: RunState) -> dict[str, Any]:
    """Итог партии.

    Безопасность весит больше лояльности (0.6 против 0.4): в ВСМ сервис не
    оплачивается риском, и это должно быть видно в баллах, а не только
    в словах инструктора.
    """
    base = round(state.safety * 0.6 + state.loyalty * 0.4)
    timeouts = sum(1 for event in state.events if event.timed_out)
    endings = [segment["ending"] for segment in state.segments] + [state.ending or "neutral"]
    bonuses = [{"good": 10, "neutral": 0, "bad": -10}.get(ending or "neutral", 0) for ending in endings]
    ending_bonus = round(sum(bonuses) / len(bonuses))
    total = clamp(base + ending_bonus - 3 * timeouts)   # итог всегда в шкале 0..100
    grade = next(name for threshold, name in GRADES if total >= threshold)
    return {
        "loyalty": state.loyalty,
        "safety": state.safety,
        "ending": state.ending,
        "score": total,
        "xp": total * scenario.difficulty,
        "grade": grade,
        "timeouts": timeouts,
        "trip_id": state.trip_id,
        "segments": [*state.segments, {"scenario_id": state.scenario_id, "ending": state.ending}],
        "competences": dict(state.competences),
        "weak": sorted(k for k, v in state.competences.items() if v < 0),
        "strong": sorted(k for k, v in state.competences.items() if v >= 3),
    }
