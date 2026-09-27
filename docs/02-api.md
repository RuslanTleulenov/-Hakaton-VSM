# API

База: `/api/v1`. Живая схема OpenAPI — `/openapi.json`, Swagger UI — `/docs`.
Все ответы — JSON, кодировка UTF-8.

## Служебное

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/health` | статус стенда, число сценариев и достижений |
| GET | `/reference` | справочники: пять компетенций и шаги ролевой модели |

## Профиль

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/conductors` | завести/получить профиль (демо-вход по логину) |
| GET | `/conductors/{login}` | профиль: уровень, опыт, компетенции, достижения, история |

```json
POST /api/v1/conductors
{"login": "a.smirnova", "display_name": "Смирнова А.",
 "brigade": "Бригада 3", "depot": "Депо Москва-Пассажирская"}
```

## Сценарии и партия

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/scenarios?login=` | каталог; с `login` порядок адаптивный — сверху непройденные и худшие |
| POST | `/runs` | начать рейс: `{"login": "...", "scenario_id": "medical"}` |
| POST | `/runs/{run_id}/choose` | ход: `{"option_id": "radio"}` или `{"option_id": null}` — не успел |
| GET | `/runs/{run_id}/debrief` | разбор: ходы, причины, «как лучше», советы, источники |

Ответ на ход:

```json
{
  "run_id": "0f2c…",
  "loyalty": 78, "safety": 100, "finished": false,
  "node": {"node_id": "care", "text": "…", "speaker": "passenger",
           "timer": 20, "critical": false,
           "options": [{"id": "empathy", "text": "…", "step": "acknowledge"}]},
  "event": {"option_text": "…", "loyalty_delta": 6, "safety_delta": 15,
            "competence_deltas": {"safety": 3, "teamwork": 3},
            "seconds": 4.8, "timer": 25, "timed_out": false,
            "reasons": ["Вызов через начальника поезда — штатный порядок…"],
            "better": null}
}
```

Когда партия завершилась, в ответе появляется `result` с баллом, оценкой,
опытом и заработанными достижениями.

**Время решения считает сервер.** Клиент не передаёт длительность: в БД лежит
момент показа узла (`node_shown_at`), и при ходе разница берётся по серверным
часам. `option_id: null` — это «игрок не успел», окончательное решение
принимает ядро.

## Геймификация и аналитика

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/leaderboard?scope=company\|brigade\|depot&value=` | рейтинг по опыту |
| GET | `/notifications?login=` | новые сценарии, челленджи, сгорающие баллы |
| POST | `/notifications/{id}/read` | отметить прочитанным |
| GET | `/analytics/hotspots?limit=` | развилки с наибольшей потерей шкал |

## Коды ошибок

| Код | Когда |
|---|---|
| 404 | нет сценария, партии или проводника |
| 409 | вариант недоступен по флагам, ход в уже завершённой партии |
| 422 | некорректное тело запроса или `scope` вне списка |

## Пример: партия целиком через curl

```bash
curl -s -X POST localhost:8040/api/v1/conductors \
  -H 'Content-Type: application/json' \
  -d '{"login":"demo","display_name":"Демо","brigade":"Бригада 1","depot":"Депо Тверь"}'

RUN=$(curl -s -X POST localhost:8040/api/v1/runs -H 'Content-Type: application/json' \
  -d '{"login":"demo","scenario_id":"medical"}' | python -c 'import sys,json;print(json.load(sys.stdin)["run_id"])')

curl -s -X POST localhost:8040/api/v1/runs/$RUN/choose -H 'Content-Type: application/json' -d '{"option_id":"ask"}'
curl -s localhost:8040/api/v1/runs/$RUN/debrief
```
