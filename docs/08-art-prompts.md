# Арт для лайт-новеллы: контракт и промпты

Три сценария дневного рейса 751 собраны как лайт-новелла: фон сцены,
персонаж со сменой эмоции и печатающаяся реплика.

**Арт сгенерирован и подключён** — 3 фона и 28 спрайтов лежат в
`frontend/assets/`. Этот документ нужен, чтобы дорисовать персонажей для
новых сценариев в том же стиле: промпты ниже — те самые, по которым сделан
текущий комплект.

Подключение — **без единой строки кода**: файл с нужным именем кладётся
в папку. Если файла нет, сцена рисуется векторной подложкой, а имя
персонажа показывается табличкой — демонстрация не ломается.

## Куда класть файлы

```
frontend/assets/scenes/<scene>.jpg          фон, 1920×1080, JPG, до 400 КБ
frontend/assets/characters/<sprite>-<mood>.png   спрайт, 900×1400, PNG с прозрачностью, до 500 КБ
```

Имена сцен и спрайтов берутся из сценария (`content/scenarios/*.yaml`,
поля `scene` и `characters`), настроения — из `domain.MOODS`:

| mood | когда показывается |
|---|---|
| `calm` | спокоен, нейтральное начало |
| `pleased` | доволен, конфликт снят |
| `tense` | напряжён, ситуация обостряется |
| `upset` | на взводе, пик конфликта или паника |

Итого нужно: **3 фона** и **7 персонажей × 4 эмоции = 28 спрайтов**.

## Общий стиль (добавлять к каждому промпту)

> Semi-realistic digital illustration, clean modern visual-novel style,
> soft cinematic lighting, muted premium palette: warm beige, graphite grey,
> deep navy, single restrained red accent. High-speed train interior,
> contemporary Russian railway service aesthetic. No text, no logos,
> no watermarks, no brand names. Calm, respectful tone — this is a training
> simulator for staff, not a drama poster.

**Negative prompt** (во все генерации):

> text, letters, logos, watermark, brand names, cartoon exaggeration, anime
> big eyes, horror, blood, gore, distorted hands, extra limbs, low quality,
> jpeg artifacts, cluttered background, lens flare overload

**Консистентность.** Каждого персонажа генерируйте **одной серией из
четырёх кадров** (или через seed / character reference), меняя только
выражение лица и позу: одежда, причёска, возраст и телосложение обязаны
совпадать во всех четырёх спрайтах. Иначе при смене эмоции персонаж
«превратится» в другого человека.

---

## История 1. «Два пассажира на одно место» (вагон бизнес-класса, день)

### Фон `business-day.jpg`

> Interior of a modern high-speed train business-class car, 2+2 seating,
> wide beige leather seats with dark wood tables, large window with blurred
> summer landscape rushing past, bright daylight, aisle receding into depth,
> overhead luggage racks, clean minimal design. Empty aisle in the
> foreground-left so a character can stand there. Camera at seated eye
> level, slight wide angle. No people in focus, a few blurred silhouettes
> far in the background.

### `sergey-*.png` — Сергей, пассажир с чемоданом

Мужчина 35–40 лет, деловой casual: тёмно-синее поло, светлые брюки,
короткая стрижка, в правой руке ручка чемодана-каррибега. Стоит
вполоборота, кадр по колено.

| Файл | Промпт (к общему стилю) |
|---|---|
| `sergey-calm.png` | Full-body man in his late thirties, navy polo shirt, light trousers, short dark hair, holding a carry-on suitcase handle, standing three-quarter view, neutral polite expression, relaxed shoulders. Transparent background, soft rim light from the left. |
| `sergey-pleased.png` | Same man, same clothes and hair, slight grateful smile, shoulders dropped, suitcase lowered to the floor, head tilted slightly, warm expression. Transparent background. |
| `sergey-tense.png` | Same man, same clothes, eyebrows drawn together, lips pressed, ticket held up in one hand, weight shifted forward, impatient but controlled. Transparent background. |
| `sergey-upset.png` | Same man, same clothes, openly indignant: chin up, free hand gesturing toward a seat, jaw tight, suitcase pushed aside. Still restrained, not aggressive. Transparent background. |

### `igor-*.png` — Игорь, пассажир у окна

Мужчина 45–50 лет, серый пиджак поверх белой рубашки, очки, седина
на висках. Сидит в кресле, кадр по пояс, слегка снизу.

| Файл | Промпт |
|---|---|
| `igor-calm.png` | Seated man in his late forties, grey blazer over white shirt, thin glasses, greying temples, sitting in a train seat by the window, looking forward with composed neutral expression. Transparent background. |
| `igor-pleased.png` | Same seated man, same clothes and glasses, faint satisfied smile, relaxed hands on the armrest, looking slightly up as if thanking someone. Transparent background. |
| `igor-tense.png` | Same seated man, same clothes, demonstratively turned toward the window, arms folded, mouth a straight line, avoiding eye contact. Transparent background. |
| `igor-upset.png` | Same seated man, same clothes, holding a smartphone up as if filming, eyebrows raised in confrontation, body turned toward the viewer. Transparent background. |

### `chief-*.png` — Ольга Петровна, начальник поезда

Женщина 40–45 лет, форменный тёмно-синий китель с красным кантом,
белая рубашка, волосы собраны, бейдж без надписей. Кадр по пояс.
**Используется и в истории 3** — генерировать один раз.

| Файл | Промпт |
|---|---|
| `chief-calm.png` | Woman in her early forties, navy railway service uniform jacket with a thin red trim, white shirt, hair in a neat bun, blank badge (no text), calm professional expression, hands relaxed. Transparent background. |
| `chief-pleased.png` | Same woman, same uniform and hairstyle, approving slight smile, nodding gesture, one hand gesturing acknowledgement. Transparent background. |
| `chief-tense.png` | Same woman, same uniform, focused serious expression, radio handset raised near the shoulder, attentive posture. Transparent background. |
| `chief-upset.png` | Same woman, same uniform, stern disappointed expression, arms slightly forward, demanding an explanation. Professional, never shouting. Transparent background. |

---

## История 2. «Ребёнок потерялся» (служебная зона у тамбура)

### Фон `service-zone.jpg`

> Service area of a modern high-speed train near the vestibule door: narrow
> galley with brushed-metal counter, coffee machine, folded service trolley,
> closed automatic door with a round porthole window, cooler daylight from
> the vestibule, teal-grey palette, slightly cramped and functional. Camera
> at adult eye level, empty floor space in the foreground centre.

### `misha-*.png` — Миша, шесть лет

Мальчик шести лет, жёлтая футболка с абстрактным принтом (без надписей),
джинсовые шорты, кроссовки, тёмные волосы, в руках маленький рюкзак.
Кадр в полный рост, ракурс сверху вниз — глазами взрослого.

| Файл | Промпт |
|---|---|
| `misha-calm.png` | Full-body six-year-old boy, yellow t-shirt with an abstract pattern (no text), denim shorts, sneakers, dark hair, holding a small backpack, standing still, neutral slightly shy expression, viewed slightly from above. Transparent background. |
| `misha-pleased.png` | Same boy, same clothes, shy relieved smile, holding a children's magazine, shoulders relaxed, looking up. Transparent background. |
| `misha-tense.png` | Same boy, same clothes, clutching the backpack to his chest, wide worried eyes, looking around, one hand gripping a counter edge. Transparent background. |
| `misha-upset.png` | Same boy, same clothes, crying quietly: tears on cheeks, mouth turned down, rubbing one eye with a fist, standing alone. Handled gently and respectfully, not melodramatic. Transparent background. |

### `anna-*.png` — Анна, мама Миши

Женщина 30–35 лет, светлый свитер, джинсы, волосы собраны в хвост,
в руке телефон. Кадр по колено.

| Файл | Промпт |
|---|---|
| `anna-calm.png` | Woman in her early thirties, light knit sweater, jeans, ponytail, phone in one hand, calm searching expression, walking pose. Transparent background. |
| `anna-pleased.png` | Same woman, same clothes and ponytail, relieved warm smile, one hand pressed to her chest, the other reaching down toward a child. Transparent background. |
| `anna-tense.png` | Same woman, same clothes, anxious expression, scanning the car, phone raised as if about to call. Transparent background. |
| `anna-upset.png` | Same woman, same clothes, upset and accusing: eyebrows drawn, one hand gesturing, protective stance, speaking sharply but not screaming. Transparent background. |

---

## История 3. «Пассажиру стало плохо» (комфорт-класс, место у окна)

### Фон `comfort-window.jpg`

> Interior of a modern high-speed train comfort-class car near a window
> seat, 2+2 layout, warm beige seats, small table with a paper coffee cup,
> late-afternoon golden light through a large window with blurred fields,
> soft shadows, a few blurred passengers in the background. Camera at
> standing attendant height looking slightly down at an empty seat in the
> left foreground.

### `elena-*.png` — Елена, пассажирка места 12

Женщина 55–60 лет, бежевый кардиган поверх блузки, короткая стрижка,
очки на цепочке. Сидит в кресле, кадр по пояс.

| Файл | Промпт |
|---|---|
| `elena-calm.png` | Seated woman around sixty, beige cardigan over a blouse, short grey-brown hair, glasses on a chain, sitting by a train window, composed neutral expression, hands in her lap. Transparent background. |
| `elena-pleased.png` | Same seated woman, same cardigan and hairstyle, faint grateful smile, holding a glass of water with both hands, colour returning to her face. Transparent background. |
| `elena-tense.png` | Same seated woman, same clothes, pale face, one hand pressed to her chest, shallow breathing, leaning slightly back into the seat, worried eyes. Medical discomfort shown respectfully, no distress porn. Transparent background. |
| `elena-upset.png` | Same seated woman, same clothes, embarrassed and overwhelmed: covering her face with one hand, turning toward the window, shoulders drawn in. Transparent background. |

### `viktor-*.png` — Виктор, пассажир через проход

Мужчина 30–35 лет, худи и наушники на шее, в руке телефон.
Кадр по пояс, сидит вполоборота.

| Файл | Промпт |
|---|---|
| `viktor-calm.png` | Seated man in his early thirties, grey hoodie, headphones around his neck, phone in hand resting on the table, neutral incurious expression, three-quarter view. Transparent background. |
| `viktor-pleased.png` | Same seated man, same hoodie and headphones, approving nod, phone put face-down on the table, relaxed friendly expression. Transparent background. |
| `viktor-tense.png` | Same seated man, same clothes, leaning into the aisle, curious and judging, phone half-raised. Transparent background. |
| `viktor-upset.png` | Same seated man, same clothes, openly filming with the phone held up, confrontational expression, other hand gesturing. Transparent background. |

---

## Проверка перед подключением

1. Спрайт — PNG с **прозрачным** фоном, обрезан по силуэту, персонаж стоит
   на нижней границе кадра (ноги/обрез не «висят» в воздухе).
2. Все четыре эмоции одного персонажа — один и тот же человек: одежда,
   причёска, возраст, телосложение.
3. Никаких надписей, логотипов и узнаваемого фирменного стиля перевозчика:
   бейджи и таблички должны быть пустыми.
4. Файл лежит по точному пути и называется ровно как в таблице.
5. Проверка: `python backend/validate.py`, затем открыть сценарий в
   интерфейсе — картинка подхватится сразу, перезапуск не нужен.

Если какого-то файла нет, интерфейс молча уберёт картинку и покажет
градиент и табличку с именем — сломанных иконок на демонстрации не будет.
