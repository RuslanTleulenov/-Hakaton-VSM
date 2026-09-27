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
| GET | `/trips` | рейсы: несколько инцидентов подряд с общими шкалами и памятью |
| POST | `/runs` | начать: `{"login": "...", "scenario_id": "medical"}` или `{"login": "...", "trip_id": "day-751", "challenge": false}` |
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
опытом, серией и заработанными достижениями.

В рейсе ответ дополняется двумя полями:

```json
"trip": {"id": "day-751", "title": "Дневной рейс 751", "position": 2, "total": 3,
         "memory": [{"flag": "goodwill_car", "label": "Салон на вашей стороне — спор решён по-человечески"}]},
"segment_done": {"scenario_id": "double-seat", "ending": "good", "text": "…"}
```

`segment_done` приходит один раз — в тот ход, которым закончился инцидент:
интерфейс показывает итог перегона, а партия уже стоит на первом узле
следующего инцидента. Шкалы и память при этом не обнуляются.

У каждого хода может быть `alternative` — ветка, которую игрок не выбрал,
если она была заметно лучше:

```json
"alternative": {"option_id": "ask", "text": "Подойти: «Я рядом…»",
                "reason": "Признание ситуации и оценка состояния — первый шаг по методичке",
                "loyalty": 8, "safety": 4}
```

**Время решения считает сервер.** Клиент не передаёт длительность: в БД лежит
момент показа узла (`node_shown_at`), и при ходе разница берётся по серверным
часам. `option_id: null` — это «игрок не успел», окончательное решение
принимает ядро.

## Геймификация и аналитика

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/leaderboard?scope=company\|brigade\|depot&value=` | рейтинг по опыту |
| GET | `/challenge?login=` | рейс недели: сценарий, бонус, отдельная таблица |
| GET | `/conductors/{login}/streak` | серия дней и сгорающие баллы челленджа |
| GET | `/notifications?login=` | новые сценарии, челленджи, сгорающие баллы |
| POST | `/notifications/{id}/read` | отметить прочитанным |
| GET | `/analytics/hotspots?limit=` | развилки с наибольшей потерей шкал |
| GET | `/analytics/trend?login=&limit=` | динамика компетенций по последним рейсам |

## Коды ошибок

| Код | Когда |
|---|---|
| 404 | нет сценария, партии или проводника |
| 409 | вариант недоступен по флагам, ход в уже завершённой партии |
| 422 | некорректное тело запроса, `scope` вне списка, нет заголовка `X-API-Key` |
| 401 | токен интеграции неизвестен |

## Интеграция с HR и LMS

Отдельный раздел, закрытый заголовком `X-API-Key`. Токен выдаётся
администратором стенда и хранится в таблице `api_clients`; демо-токен
печатает `backend/seed.py`.

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/integration/progress?depot=&brigade=` | выгрузка учебного прогресса |
| POST | `/integration/assign` | назначить проводнику сценарий или рейс |

```bash
curl -s -H 'X-API-Key: demo-hr-…'   'localhost:8040/api/v1/integration/progress?depot=Депо%20Тверь'
```

```json
{"client": "HR-портал (демо)", "generated_at": "2026-09-28T…",
 "conductors": [{"login": "s.voronina", "brigade": "Бригада 7", "depot": "Депо Тверь",
                 "level": "Старший проводник", "xp": 2012, "runs_completed": 9,
                 "average_score": 85, "competences": {"safety": 21, "…": 0},
                 "weak_competences": ["composure"], "achievements": ["first-run", "full-trip"],
                 "streak_days": 1}]}
```

ФИО во внешнюю систему не уходит: HR знает сотрудника по учётной записи,
тренажёру личные данные не нужны (см. [`06-security.md`](06-security.md)).

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
