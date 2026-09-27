"""Доменные типы тренажёра: сценарий, узел, вариант ответа, состояние партии.

Сценарий — данные (YAML), а не код: методист добавляет ситуацию без
программиста. Здесь описано только то, что движок умеет исполнять.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Пять компетенций проводника ВСМ. Ключи используются в YAML сценариев.
COMPETENCES = {
    "safety": "Регламент и безопасность",
    "deescalation": "Деэскалация",
    "service": "Эмпатия и сервис",
    "composure": "Хладнокровие",
    "teamwork": "Работа с бригадой",
}

# Шаги ролевой модели из методички «Примеры ситуаций взаимодействия
# поездного персонала с пассажирами»: признать → правило → решение → заверить.
STEPS = {
    "acknowledge": "Признать ситуацию",
    "rule": "Обозначить правило",
    "solution": "Предложить решение",
    "assure": "Заверить",
    "action": "Действие без слов",
}


@dataclass(frozen=True)
class Effects:
    """Что вариант делает со шкалами, компетенциями и флагами партии."""

    loyalty: int = 0
    safety: int = 0
    competences: dict[str, int] = field(default_factory=dict)
    set_flags: list[str] = field(default_factory=list)
    clear_flags: list[str] = field(default_factory=list)

    @staticmethod
    def parse(raw: dict[str, Any] | None) -> "Effects":
        raw = raw or {}
        unknown = set(raw.get("competences", {})) - set(COMPETENCES)
        if unknown:
            raise ValueError(f"неизвестные компетенции: {sorted(unknown)}")
        return Effects(
            loyalty=int(raw.get("loyalty", 0)),
            safety=int(raw.get("safety", 0)),
            competences={k: int(v) for k, v in raw.get("competences", {}).items()},
            set_flags=list(raw.get("set", [])),
            clear_flags=list(raw.get("clear", [])),
        )


@dataclass(frozen=True)
class Branch:
    """Условный переход: если флаг взведён, ход идёт в другой узел.

    Так работает память пассажиров между инцидентами рейса: пассажир,
    которому отказали на первом перегоне, встречает проводника иначе.
    """

    flag: str
    goto: str


@dataclass(frozen=True)
class Option:
    """Вариант действия проводника в узле сценария."""

    id: str
    text: str
    goto: str
    reason: str                      # почему шкалы изменились — показывается в разборе
    step: str | None = None          # шаг ролевой модели
    effects: Effects = Effects()
    requires: list[str] = field(default_factory=list)      # нужны эти флаги
    forbidden: list[str] = field(default_factory=list)     # недоступен при этих флагах
    better: str | None = None        # «как можно было лучше» для обучающей обратной связи
    goto_if: list[Branch] = field(default_factory=list)    # условные переходы, проверяются по порядку

    def available(self, flags: set[str]) -> bool:
        return all(f in flags for f in self.requires) and not any(f in flags for f in self.forbidden)

    def target(self, flags: set[str]) -> str:
        """Куда ведёт ход с учётом памяти о прошлых инцидентах."""
        for branch in self.goto_if:
            if branch.flag in flags:
                return branch.goto
        return self.goto


@dataclass(frozen=True)
class Timeout:
    """Что происходит, если проводник не успел решить."""

    goto: str
    reason: str
    effects: Effects = Effects()


@dataclass(frozen=True)
class Node:
    """Узел сценария: реплика/событие и варианты ответа."""

    id: str
    text: str
    speaker: str = "narrator"        # passenger | radio | narrator | chief
    timer: int | None = None         # секунды на решение; None — без таймера
    critical: bool = False           # критическое решение (влияет на хладнокровие)
    options: list[Option] = field(default_factory=list)
    timeout: Timeout | None = None
    ending: str | None = None        # good | neutral | bad — узел финальный

    @property
    def is_final(self) -> bool:
        return self.ending is not None


@dataclass(frozen=True)
class Scenario:
    """Сценарий = один инцидент на маршруте."""

    id: str
    title: str
    summary: str
    segment: str                     # перегон, напр. «Москва — Тверь»
    minutes_to_stop: int             # минут до остановки: ограничивает «станционные» действия
    car_class: str                   # класс обслуживания вагона
    difficulty: int                  # 1..3
    sources: list[str]               # ссылки на регламент/методичку
    start: str
    nodes: dict[str, Node]
    start_loyalty: int = 70
    start_safety: int = 80

    def node(self, node_id: str) -> Node:
        try:
            return self.nodes[node_id]
        except KeyError:
            raise ValueError(f"сценарий {self.id}: нет узла {node_id!r}") from None


@dataclass(frozen=True)
class Trip:
    """Рейс — несколько инцидентов подряд с общей памятью и общими шкалами.

    Это главное отличие от набора отдельных ситуаций: пассажир, которому
    отказали в первом вагоне, встречается снова на третьем перегоне, а шкалы
    не обнуляются между инцидентами — как в настоящей смене.
    """

    id: str
    title: str
    summary: str
    route: str
    segments: list[str]              # id сценариев по порядку следования
    memory_labels: dict[str, str] = field(default_factory=dict)  # флаг → что это значит для игрока
    start_loyalty: int = 70
    start_safety: int = 85
