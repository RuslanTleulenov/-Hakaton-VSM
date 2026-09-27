/* Презентация проекта «Перегон» — тренажёр проводника ВСМ. */
const pptxgen = require("pptxgenjs");
const path = require("path");

const SHOTS = path.join(__dirname, "shots");   // скриншоты снимает shots.py
const shot = (name) => path.join(SHOTS, name);

const C = {
  ink: "0E1420",
  inkSoft: "172033",
  line: "2B3950",
  white: "FFFFFF",
  light: "F4F6FA",
  text: "141A24",
  muted: "5B6B85",
  mutedDark: "9AA8BF",
  red: "D6001C",
  green: "1F9D5F",
  blue: "2F6FD0",
  amber: "C77A00",
};

const F = { head: "Arial", body: "Arial" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 × 7.5
pres.author = "Команда проекта «Перегон»";
pres.title = "Перегон — тренажёр проводника ВСМ";

const W = 13.33;
const M = 0.7;

/* --- помощники ---------------------------------------------------------- */

function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: C.ink };
  return s;
}

function lightSlide(title, kicker) {
  const s = pres.addSlide();
  s.background = { color: C.white };
  if (kicker) {
    s.addText(kicker.toUpperCase(), {
      x: M, y: 0.42, w: 9, h: 0.25,
      fontFace: F.body, fontSize: 11, bold: true, color: C.red, charSpacing: 1.6,
      isTextBox: true, margin: 0,
    });
  }
  s.addText(title, {
    x: M, y: kicker ? 0.68 : 0.5, w: W - 2 * M, h: 0.75,
    fontFace: F.head, fontSize: 32, bold: true, color: C.text,
    isTextBox: true, margin: 0,
  });
  return s;
}

function card(s, { x, y, w, h, fill = C.light, line = "E3E8F0" }) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.12,
    fill: { color: fill }, line: { color: line, width: 1 },
  });
}

function badge(s, { x, y, text, color = C.red, size = 0.42 }) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: size, h: size, fill: { color } });
  s.addText(text, {
    x, y, w: size, h: size, align: "center", valign: "middle",
    fontFace: F.head, fontSize: 13, bold: true, color: C.white, isTextBox: true, margin: 0,
  });
}

function stat(s, { x, y, w, value, label, color = C.red }) {
  s.addText(value, {
    x, y, w, h: 0.72, fontFace: F.head, fontSize: 40, bold: true, color,
    isTextBox: true, margin: 0,
  });
  s.addText(label, {
    x, y: y + 0.72, w, h: 0.5, fontFace: F.body, fontSize: 12, color: C.muted,
    isTextBox: true, margin: 0,
  });
}

/* --- 1. титул ----------------------------------------------------------- */
{
  const s = darkSlide();
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 1.35, w: 1.5, h: 1.5, rectRadius: 0.2, fill: { color: C.red },
  });
  s.addText("ВСМ", {
    x: M, y: 1.35, w: 1.5, h: 1.5, align: "center", valign: "middle",
    fontFace: F.head, fontSize: 30, bold: true, color: C.white, isTextBox: true, margin: 0,
  });
  s.addText("Перегон", {
    x: 2.5, y: 1.4, w: 8, h: 1.1,
    fontFace: F.head, fontSize: 60, bold: true, color: C.white, isTextBox: true, margin: 0,
  });
  s.addText("геймифицированный тренажёр проводника высокоскоростной магистрали", {
    x: 2.52, y: 2.5, w: 9.5, h: 0.5,
    fontFace: F.body, fontSize: 17, color: C.mutedDark, isTextBox: true, margin: 0,
  });
  s.addText(
    "Одна тренировка — один рейс Москва — Санкт-Петербург, сжатый до 15 минут.\nРешения за секунды, последствия на весь рейс, разбор со ссылкой на регламент.",
    { x: M, y: 3.6, w: 10.5, h: 1.1, fontFace: F.body, fontSize: 16, color: C.white, lineSpacing: 26, isTextBox: true, margin: 0 }
  );
  ["6 сценариев", "2 рейса по 3 инцидента", "53 узла · 92 варианта", "33 теста"].forEach((t, i) => {
    const x = M + i * 3.02;
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 5.1, w: 2.8, h: 0.62, rectRadius: 0.31,
      fill: { color: C.inkSoft }, line: { color: C.line, width: 1 },
    });
    s.addText(t, {
      x, y: 5.1, w: 2.8, h: 0.62, align: "center", valign: "middle",
      fontFace: F.body, fontSize: 13, color: C.white, isTextBox: true, margin: 0,
    });
  });
  s.addText("Хакатон Московского транспорта · трек «Геймификация для ВСМ»", {
    x: M, y: 6.5, w: 11, h: 0.4, fontFace: F.body, fontSize: 13, color: C.mutedDark, isTextBox: true, margin: 0,
  });
  s.addNotes(
    "Мы сделали тренажёр, где проводник ВСМ проживает нештатные ситуации целым рейсом, " +
    "а не отвечает на вопросы теста. Дальше покажу три вещи, которых нет в обычном квизе с таймером."
  );
}

/* --- 2. проблема -------------------------------------------------------- */
{
  const s = lightSlide("Тест проверяет знание регламента.\nОн не проверяет поведение под давлением.", "Проблема");
  const items = [
    ["1", "Стресс и дефицит времени", "В вагоне на 400 км/ч решение принимается за секунды. Лекция и тест этому не учат: там можно подумать и перечитать."],
    ["2", "Нет безопасной среды", "Отрабатывать конфликт или медицинский инцидент на реальных пассажирах нельзя. Ошибка стоит и безопасности, и репутации премиального сервиса."],
    ["3", "Soft skills не измеряются", "«Умеет успокоить пассажира» — это не галочка в тесте. Нужна оценка, которую можно показать сотруднику и методисту."],
  ];
  items.forEach(([n, title, body], i) => {
    const x = M + i * 4.13;
    card(s, { x, y: 2.5, w: 3.9, h: 2.9 });
    badge(s, { x: x + 0.3, y: 2.8, text: n });
    s.addText(title, {
      x: x + 0.3, y: 3.4, w: 3.3, h: 0.5, fontFace: F.head, fontSize: 16, bold: true, color: C.text,
      isTextBox: true, margin: 0,
    });
    s.addText(body, {
      x: x + 0.3, y: 3.95, w: 3.3, h: 1.3, fontFace: F.body, fontSize: 12, color: C.muted,
      lineSpacing: 18, isTextBox: true, margin: 0,
    });
  });
  s.addText(
    "Данные кейса: методичка «Примеры ситуаций взаимодействия поездного персонала с пассажирами» — 51 ситуация с эталонными реакциями, стандарты СТО РЖД по обслуживанию пассажиров ВСМ.",
    { x: M, y: 5.75, w: W - 2 * M, h: 0.6, fontFace: F.body, fontSize: 12, italic: true, color: C.muted, isTextBox: true, margin: 0 }
  );
  s.addNotes("Проводник знает регламент. Вопрос в том, вспомнит ли он его, когда в вагоне одновременно плачет ребёнок и пассажиру плохо.");
}

/* --- 3. идея ------------------------------------------------------------ */
{
  const s = darkSlide();
  s.addText("ИДЕЯ", {
    x: M, y: 0.5, w: 6, h: 0.3, fontFace: F.body, fontSize: 11, bold: true, color: C.red, charSpacing: 1.6, isTextBox: true, margin: 0,
  });
  s.addText("Тренировка — это рейс, а не набор вопросов", {
    x: M, y: 0.85, w: W - 2 * M, h: 0.8, fontFace: F.head, fontSize: 32, bold: true, color: C.white, isTextBox: true, margin: 0,
  });
  s.addText(
    "Смена проводника: несколько нештатных ситуаций подряд на маршруте Москва — Санкт-Петербург. " +
    "Шкалы не обнуляются между инцидентами, а пассажиры помнят, как с ними обошлись на прошлом перегоне.",
    { x: M, y: 1.75, w: 11.5, h: 0.8, fontFace: F.body, fontSize: 15, color: C.mutedDark, lineSpacing: 22, isTextBox: true, margin: 0 }
  );
  const tiles = [
    ["Таймер от маршрута", "Медиков вызывают к платформе, пассажира передают полиции на вокзале. Не успел до станции — вариант закрылся.", C.amber],
    ["Две шкалы", "«Лояльность пассажира» и «рейтинг безопасности» тянут в разные стороны. Безопасность не торгуется.", C.blue],
    ["Память пассажиров", "Салон, с которым нашли общий язык, помогает. Видевший публичный спор — достаёт телефон.", C.green],
    ["Разбор со ссылкой", "Каждый балл объяснён причиной и пунктом методички. Плюс ветка, которую вы не выбрали.", C.red],
  ];
  tiles.forEach(([title, body, color], i) => {
    const x = M + i * 3.02;
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 2.9, w: 2.8, h: 2.7, rectRadius: 0.14,
      fill: { color: C.inkSoft }, line: { color: C.line, width: 1 },
    });
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.28, y: 3.2, w: 0.26, h: 0.26, fill: { color } });
    s.addText(title, {
      x: x + 0.28, y: 3.6, w: 2.25, h: 0.6, fontFace: F.head, fontSize: 15, bold: true, color: C.white, isTextBox: true, margin: 0,
    });
    s.addText(body, {
      x: x + 0.28, y: 4.22, w: 2.25, h: 1.3, fontFace: F.body, fontSize: 11.5, color: C.mutedDark, lineSpacing: 16, isTextBox: true, margin: 0,
    });
  });
  s.addText("Всё это — данные, а не код: методист добавляет ситуацию из методички без программиста.", {
    x: M, y: 5.95, w: 11.5, h: 0.5, fontFace: F.body, fontSize: 13, color: C.white, isTextBox: true, margin: 0,
  });
  s.addNotes("Ключевая мысль слайда: рейс, а не квиз. И лояльность здесь — ресурс, который работает дальше по смене.");
}

/* --- 4. как это выглядит ------------------------------------------------ */
{
  const s = lightSlide("Инцидент подаётся как лайт-новелла", "Интерфейс");
  s.addImage({ path: shot("02-novel.png"), x: M, y: 1.75, w: 7.5, h: 5.2, sizing: { type: "contain", w: 7.5, h: 5.2 } });
  const notes = [
    ["Сцена и персонаж", "Фон вагона и собеседник со сменой эмоции: спокоен → доволен → напряжён → на взводе."],
    ["Обе шкалы сверху", "Видно последствие каждого решения сразу, а не только в конце."],
    ["Таймер от сервера", "Браузер не передаёт время: момент показа узла лежит в базе. Подкрутить таймер из консоли нельзя."],
    ["Шаг ролевой модели", "У каждого варианта подписан шаг: признать → правило → решение → заверить."],
  ];
  notes.forEach(([t, b], i) => {
    const y = 1.9 + i * 1.25;
    s.addShape(pres.ShapeType.ellipse, { x: 8.55, y: y + 0.06, w: 0.2, h: 0.2, fill: { color: C.red } });
    s.addText(t, { x: 8.95, y, w: 3.7, h: 0.35, fontFace: F.head, fontSize: 15, bold: true, color: C.text, isTextBox: true, margin: 0 });
    s.addText(b, { x: 8.95, y: y + 0.36, w: 3.7, h: 0.8, fontFace: F.body, fontSize: 11.5, color: C.muted, lineSpacing: 16, isTextBox: true, margin: 0 });
  });
  s.addNotes("Режим новеллы включается для сценариев, у которых есть сцена. Арт подключается файлами, без кода; пока его нет — векторная подложка.");
}

/* --- 5. движок ---------------------------------------------------------- */
{
  const s = lightSlide("Сценарий — это данные, а не код", "Движок сценариев");
  card(s, { x: M, y: 1.8, w: 6.9, h: 4.5, fill: "0E1420", line: "0E1420" });
  const yaml = [
    "options:",
    "  - id: radio",
    "    step: solution           # шаг ролевой модели",
    "    text: «Вызвать начальника поезда и попросить",
    "           медиков к платформе в Твери»",
    "    reason: Вызов через начальника поезда —",
    "            штатный порядок (ситуация 19)",
    "    effects:",
    "      loyalty: 6",
    "      safety: 15",
    "      competences: {safety: 3, teamwork: 3}",
    "      set: [medics_called]   # память рейса",
    "    goto_if:",
    "      - flag: car_tense      # вагон помнит спор",
    "        goto: filmed",
    "    goto: care",
  ].join("\n");
  s.addText(yaml, {
    x: M + 0.25, y: 2.05, w: 6.4, h: 4,
    fontFace: "Courier New", fontSize: 10.5, color: "D7E3F5", lineSpacing: 15, isTextBox: true, margin: 0,
  });
  const stats = [
    ["6", "сценариев из методички", C.red],
    ["53", "узла, 92 варианта ответа", C.blue],
    ["2", "рейса по три инцидента", C.green],
    ["12", "достижений", C.amber],
  ];
  stats.forEach(([v, l, color], i) => {
    const x = 8.0 + (i % 2) * 2.7;
    const y = 1.9 + Math.floor(i / 2) * 1.5;
    stat(s, { x, y, w: 2.5, value: v, label: l, color });
  });
  s.addText(
    "Загрузчик проверяет файл целиком: битая ссылка между узлами, таймер без ветки «время вышло», недостижимый узел — " +
    "ошибка при старте, а не в середине партии. Отдельный валидатор для методиста ловит варианты без объяснения.",
    { x: 8.0, y: 5.0, w: 4.6, h: 1.3, fontFace: F.body, fontSize: 11.5, color: C.muted, lineSpacing: 16, isTextBox: true, margin: 0 }
  );
  s.addNotes("Здесь стоит показать жюри правку вживую: поменять цену решения или добавить развилку, запустить validate.py.");
}

/* --- 6. ролевая модель -------------------------------------------------- */
{
  const s = lightSlide("Важно не только что сказано, но и в каком порядке", "Механика 1 · ролевая модель");
  const steps = ["Признать\nситуацию", "Обозначить\nправило", "Предложить\nрешение", "Заверить"];
  steps.forEach((t, i) => {
    const x = M + i * 2.75;
    s.addShape(pres.ShapeType.roundRect, {
      x, y: 2.0, w: 2.3, h: 1.1, rectRadius: 0.12, fill: { color: C.light }, line: { color: "E3E8F0", width: 1 },
    });
    s.addText(t, {
      x, y: 2.0, w: 2.3, h: 1.1, align: "center", valign: "middle",
      fontFace: F.head, fontSize: 14, bold: true, color: C.text, isTextBox: true, margin: 0,
    });
    if (i < 3) {
      s.addText("→", {
        x: x + 2.3, y: 2.0, w: 0.45, h: 1.1, align: "center", valign: "middle",
        fontFace: F.head, fontSize: 18, color: C.red, isTextBox: true, margin: 0,
      });
    }
  });
  card(s, { x: M, y: 3.45, w: 5.8, h: 2.5 });
  s.addText("Правило до признания", { x: M + 0.3, y: 3.7, w: 5.2, h: 0.4, fontFace: F.head, fontSize: 16, bold: true, color: C.text, isTextBox: true, margin: 0 });
  s.addText("«Вы пьяны, алкоголь я вам не принесу»", { x: M + 0.3, y: 4.12, w: 5.2, h: 0.4, fontFace: F.body, fontSize: 13, italic: true, color: C.muted, isTextBox: true, margin: 0 });
  s.addText("−4 лояльности сверх эффекта самой реплики", { x: M + 0.3, y: 4.6, w: 5.2, h: 0.4, fontFace: F.head, fontSize: 14, bold: true, color: C.red, isTextBox: true, margin: 0 });
  s.addText("Методичка прямо запрещает называть состояние пассажира вслух: это провоцирует агрессию.", { x: M + 0.3, y: 5.05, w: 5.2, h: 0.7, fontFace: F.body, fontSize: 11.5, color: C.muted, lineSpacing: 16, isTextBox: true, margin: 0 });

  card(s, { x: 6.85, y: 3.45, w: 5.8, h: 2.5 });
  s.addText("Решение после признания", { x: 7.15, y: 3.7, w: 5.2, h: 0.4, fontFace: F.head, fontSize: 16, bold: true, color: C.text, isTextBox: true, margin: 0 });
  s.addText("«Этот напиток предложить не могу. Позвольте предложить чай или кофе?»", { x: 7.15, y: 4.12, w: 5.2, h: 0.5, fontFace: F.body, fontSize: 13, italic: true, color: C.muted, isTextBox: true, margin: 0 });
  s.addText("+3 лояльности и +1 к компетенции «сервис»", { x: 7.15, y: 4.6, w: 5.2, h: 0.4, fontFace: F.head, fontSize: 14, bold: true, color: C.green, isTextBox: true, margin: 0 });
  s.addText("Движок сравнивает шаг текущего хода с предыдущим — отдельно от эффектов самой реплики.", { x: 7.15, y: 5.05, w: 5.2, h: 0.7, fontFace: F.body, fontSize: 11.5, color: C.muted, lineSpacing: 16, isTextBox: true, margin: 0 });

  s.addText("Правила лежат списком в engine.SEQUENCE_RULES — три записи вида «шаг X после шага Y». Меняются за минуту.", {
    x: M, y: 6.25, w: W - 2 * M, h: 0.4, fontFace: F.body, fontSize: 12, italic: true, color: C.muted, isTextBox: true, margin: 0,
  });
  s.addNotes("Это прямая реализация ролевой модели из методички кейса — четыре шага на странице 2.");
}

/* --- 7. память рейса ---------------------------------------------------- */
{
  const s = lightSlide("Пассажиры помнят прошлый перегон", "Механика 2 · память рейса");
  const chain = [
    ["Инцидент 1", "Два пассажира на одно место", C.blue],
    ["Инцидент 2", "Ребёнок потерялся", C.amber],
    ["Инцидент 3", "Пассажиру стало плохо", C.red],
  ];
  chain.forEach(([n, t, color], i) => {
    const x = M + i * 4.1;
    card(s, { x, y: 1.85, w: 3.7, h: 1.1 });
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.25, y: 2.12, w: 0.22, h: 0.22, fill: { color } });
    s.addText(n, { x: x + 0.62, y: 2.0, w: 3, h: 0.3, fontFace: F.body, fontSize: 11, color: C.muted, isTextBox: true, margin: 0 });
    s.addText(t, { x: x + 0.62, y: 2.3, w: 3, h: 0.4, fontFace: F.head, fontSize: 14, bold: true, color: C.text, isTextBox: true, margin: 0 });
    if (i < 2) {
      s.addText("→", { x: x + 3.7, y: 1.85, w: 0.4, h: 1.1, align: "center", valign: "middle", fontFace: F.head, fontSize: 18, color: C.red, isTextBox: true, margin: 0 });
    }
  });
  s.addText("Шкалы и флаги переезжают из инцидента в инцидент — это и есть память", {
    x: M, y: 3.1, w: 11.9, h: 0.4, fontFace: F.body, fontSize: 13, color: C.muted, isTextBox: true, margin: 0,
  });

  card(s, { x: M, y: 3.6, w: 5.8, h: 2.4, fill: "EAF7F0", line: "BEE3D0" });
  s.addText("Спор решён по-человечески", { x: M + 0.3, y: 3.85, w: 5.2, h: 0.4, fontFace: F.head, fontSize: 15, bold: true, color: C.green, isTextBox: true, margin: 0 });
  s.addText(
    "В медицинском инциденте открывается вариант «попросить пассажиров, с которыми вы уже нашли общий язык, помочь»: " +
    "кто-то несёт воду, кто-то придерживает проход. Лояльность перестаёт быть баллом и становится ресурсом.",
    { x: M + 0.3, y: 4.3, w: 5.2, h: 1.5, fontFace: F.body, fontSize: 12, color: C.text, lineSpacing: 17, isTextBox: true, margin: 0 }
  );

  card(s, { x: 6.85, y: 3.6, w: 5.8, h: 2.4, fill: "FBECEE", line: "F0C4CA" });
  s.addText("Был публичный спор в салоне", { x: 7.15, y: 3.85, w: 5.2, h: 0.4, fontFace: F.head, fontSize: 15, bold: true, color: C.red, isTextBox: true, margin: 0 });
  s.addText(
    "Тот же ход ведёт в другой узел: сосед через проход поднимает телефон и снимает пассажирке, которой плохо. " +
    "Появляется отдельная развилка про согласие на съёмку.",
    { x: 7.15, y: 4.3, w: 5.2, h: 1.5, fontFace: F.body, fontSize: 12, color: C.text, lineSpacing: 17, isTextBox: true, margin: 0 }
  );
  s.addText("В данных это две строчки: requires: [goodwill_car] и goto_if: [{flag: car_tense, goto: filmed}].", {
    x: M, y: 6.25, w: W - 2 * M, h: 0.4, fontFace: F.body, fontSize: 12, italic: true, color: C.muted, isTextBox: true, margin: 0,
  });
  s.addNotes("Здесь показываем экран перехода между инцидентами: «Память рейса: салон на вашей стороне».");
}

/* --- 8. время ----------------------------------------------------------- */
{
  const s = darkSlide();
  s.addText("МЕХАНИКА 3 · ВРЕМЯ", { x: M, y: 0.5, w: 6, h: 0.3, fontFace: F.body, fontSize: 11, bold: true, color: C.red, charSpacing: 1.6, isTextBox: true, margin: 0 });
  s.addText("Таймер задаёт не игра, а маршрут", { x: M, y: 0.85, w: W - 2 * M, h: 0.8, fontFace: F.head, fontSize: 32, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText(
    "Поезд на 400 км/ч не остановится по требованию: всё, что делается через станцию, нужно решить до неё.",
    { x: M, y: 1.75, w: 11.5, h: 0.5, fontFace: F.body, fontSize: 15, color: C.mutedDark, isTextBox: true, margin: 0 }
  );
  const blocks = [
    ["Окно закрывается", "Чем дольше тянешь, тем меньше остаётся мягких вариантов: часть решений просто исчезает из списка."],
    ["Бездействие — выбор", "Истёк таймер — у узла своя ветка: ситуация развивается сама, хладнокровие падает, минус три балла к итогу."],
    ["Время считает сервер", "В базе лежит момент показа узла. Браузер не передаёт длительность вообще — «подкрутить» таймер нельзя."],
    ["Быстро ≠ наугад", "Верное решение в первой половине таймера даёт +2 к хладнокровию, на исходе — минус один."],
  ];
  blocks.forEach(([t, b], i) => {
    const x = M + (i % 2) * 6.15;
    const y = 2.6 + Math.floor(i / 2) * 1.85;
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: 5.85, h: 1.6, rectRadius: 0.14, fill: { color: C.inkSoft }, line: { color: C.line, width: 1 },
    });
    s.addText(t, { x: x + 0.3, y: y + 0.22, w: 5.2, h: 0.4, fontFace: F.head, fontSize: 16, bold: true, color: C.white, isTextBox: true, margin: 0 });
    s.addText(b, { x: x + 0.3, y: y + 0.66, w: 5.25, h: 0.8, fontFace: F.body, fontSize: 12, color: C.mutedDark, lineSpacing: 17, isTextBox: true, margin: 0 });
  });
  s.addText("Честный таймер — обязательное условие честной таблицы лидеров.", {
    x: M, y: 6.4, w: 11.5, h: 0.4, fontFace: F.body, fontSize: 13, color: C.white, isTextBox: true, margin: 0,
  });
  s.addNotes("На демонстрации специально даём таймеру истечь: ситуация уходит в другую ветку, и это видно на шкалах.");
}

/* --- 9. разбор ---------------------------------------------------------- */
{
  const s = lightSlide("Не «верно / неверно», а объяснение", "Обратная связь");
  s.addImage({ path: shot("06-debrief-events.png"), x: 6.5, y: 1.75, w: 6.2, h: 4.7, sizing: { type: "contain", w: 6.2, h: 4.7 } });
  const items = [
    ["Причина у каждого балла", "«Вызов через начальника поезда — штатный порядок; медики встречают состав на остановке» со ссылкой на ситуацию из методички."],
    ["Как можно было лучше", "У слабых вариантов — прямая подсказка: что именно стоило сделать вместо этого."],
    ["Что было бы, если", "Движок показывает ветку, которую вы не выбрали, — но только когда она была заметно лучше."],
    ["Выводы о человеке", "«Безопасность просела: сначала снимается риск, потом сервис» — и подбор следующих рейсов под слабую компетенцию."],
  ];
  items.forEach(([t, b], i) => {
    const y = 1.85 + i * 1.2;
    s.addShape(pres.ShapeType.ellipse, { x: M, y: y + 0.06, w: 0.2, h: 0.2, fill: { color: C.red } });
    s.addText(t, { x: M + 0.4, y, w: 5.4, h: 0.35, fontFace: F.head, fontSize: 15, bold: true, color: C.text, isTextBox: true, margin: 0 });
    s.addText(b, { x: M + 0.4, y: y + 0.36, w: 5.4, h: 0.8, fontFace: F.body, fontSize: 11.5, color: C.muted, lineSpacing: 16, isTextBox: true, margin: 0 });
  });
  s.addNotes("Это главный учебный момент: не оценка, а объяснение с нормативной основой.");
}

/* --- 10. геймификация --------------------------------------------------- */
{
  const s = lightSlide("Цикл: действие → очки → достижения → рейтинг", "Геймификация");
  s.addImage({ path: shot("07-profile.png"), x: M, y: 1.8, w: 5.6, h: 3.5, sizing: { type: "contain", w: 5.6, h: 3.5 } });
  s.addImage({ path: shot("08-leaderboard.png"), x: 6.6, y: 1.8, w: 6.1, h: 3.5, sizing: { type: "contain", w: 6.1, h: 3.5 } });
  const items = [
    ["Профиль", "Пять компетенций, пять уровней: стажёр → наставник."],
    ["Достижения", "За поведение, а не за число попыток: «Холодная голова» — десять решений вовремя."],
    ["Рейс недели", "Один сценарий для всех бригад, отдельная таблица — сравнение честное."],
    ["Серии и баллы", "Дни подряд, сгорающие очки челленджа, уведомления о новых рейсах и назначениях."],
  ];
  items.forEach(([t, b], i) => {
    const x = M + i * 3.07;
    s.addText(t, { x, y: 5.55, w: 2.85, h: 0.3, fontFace: F.head, fontSize: 14, bold: true, color: C.text, isTextBox: true, margin: 0 });
    s.addText(b, { x, y: 5.88, w: 2.85, h: 0.9, fontFace: F.body, fontSize: 11, color: C.muted, lineSpacing: 15, isTextBox: true, margin: 0 });
  });
  s.addNotes("Рейтинг честен, потому что ядро детерминированное, а время считает сервер.");
}

/* --- 11. аналитика ------------------------------------------------------ */
{
  const s = lightSlide("Данные о реальных пробелах в подготовке", "Аналитика для методистов");
  s.addImage({ path: shot("09-analytics.png"), x: 6.4, y: 1.8, w: 6.3, h: 4.6, sizing: { type: "contain", w: 6.3, h: 4.6 } });
  s.addText(
    "Каждый ход пишется в журнал: узел, выбор, время, изменения шкал и причина. Из этого получаются два ответа, " +
    "которых не даёт ни тест, ни лекция.",
    { x: M, y: 1.85, w: 5.5, h: 0.9, fontFace: F.body, fontSize: 13, color: C.muted, lineSpacing: 19, isTextBox: true, margin: 0 }
  );
  const items = [
    ["Где ошибаются чаще всего", "Развилки с наибольшей потерей шкал по всем прохождениям: видно не «кто плохой», а какая тема не отработана."],
    ["Динамика компетенций", "Сравнение первой и второй половины рейсов сотрудника: что выросло, а что стоит на месте."],
  ];
  items.forEach(([t, b], i) => {
    const y = 3.0 + i * 1.5;
    card(s, { x: M, y, w: 5.5, h: 1.3 });
    s.addText(t, { x: M + 0.28, y: y + 0.18, w: 5, h: 0.35, fontFace: F.head, fontSize: 15, bold: true, color: C.text, isTextBox: true, margin: 0 });
    s.addText(b, { x: M + 0.28, y: y + 0.55, w: 5, h: 0.7, fontFace: F.body, fontSize: 11.5, color: C.muted, lineSpacing: 16, isTextBox: true, margin: 0 });
  });
  s.addText("Те же данные уходят в HR и LMS через документированный API.", {
    x: M, y: 6.1, w: 5.5, h: 0.4, fontFace: F.body, fontSize: 12, italic: true, color: C.muted, isTextBox: true, margin: 0,
  });
  s.addNotes("Для заказчика это главный аргумент: тренажёр не только учит, но и показывает, чему учить дальше.");
}

/* --- 12. архитектура ---------------------------------------------------- */
{
  const s = lightSlide("Модульно, без «чёрных ящиков»", "Архитектура");
  s.addImage({ path: path.join(__dirname, "arch.png"), x: M, y: 1.7, w: 8.2, h: 4.9, sizing: { type: "contain", w: 8.2, h: 4.9 } });
  const items = [
    ["Стек", "Frontend без сборки (HTML/CSS/JS), backend на FastAPI, хранилище SQLite."],
    ["Ядро отдельно", "engine.py не знает ни про HTTP, ни про БД: партия воспроизводится в тесте одной функцией."],
    ["API", "OpenAPI на /docs; интеграции с HR и LMS — отдельный раздел по токену X-API-Key."],
    ["Запуск", "Python 3.11 и одна команда. Есть Dockerfile и compose."],
  ];
  items.forEach(([t, b], i) => {
    const y = 1.85 + i * 1.2;
    s.addText(t, { x: 9.1, y, w: 3.6, h: 0.3, fontFace: F.head, fontSize: 14, bold: true, color: C.text, isTextBox: true, margin: 0 });
    s.addText(b, { x: 9.1, y: y + 0.32, w: 3.6, h: 0.85, fontFace: F.body, fontSize: 11.5, color: C.muted, lineSpacing: 16, isTextBox: true, margin: 0 });
  });
  s.addNotes("Состояние партии лежит в БД, поэтому бэкенд масштабируется горизонтально без липких сессий.");
}

/* --- 13. данные и безопасность ------------------------------------------ */
{
  const s = lightSlide("Демо-среда без персональных данных", "Безопасность и соответствие");
  const items = [
    ["Только синтетика", "Профили, бригады и депо придуманы. Пассажиры в сценариях — персонажи: ни имён из жизни, ни номеров билетов, ни документов.", C.green],
    ["Минимизация в выгрузке", "В HR уходят логин, подразделение и учебные показатели. ФИО тренажёру не нужно — и не хранится.", C.blue],
    ["Секретов в коде нет", "Токен интеграции лежит в базе и выдаётся администратором; база создаётся локально при первом запуске.", C.amber],
    ["Предсказуемые ошибки", "404 / 409 / 422 / 401 с понятным текстом, а битая ссылка в сценарии — ошибка при загрузке, а не в середине партии.", C.red],
  ];
  items.forEach(([t, b, color], i) => {
    const x = M + (i % 2) * 6.15;
    const y = 1.9 + Math.floor(i / 2) * 2.2;
    card(s, { x, y, w: 5.85, h: 1.95 });
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.3, y: y + 0.28, w: 0.24, h: 0.24, fill: { color } });
    s.addText(t, { x: x + 0.3, y: y + 0.62, w: 5.2, h: 0.4, fontFace: F.head, fontSize: 16, bold: true, color: C.text, isTextBox: true, margin: 0 });
    s.addText(b, { x: x + 0.3, y: y + 1.04, w: 5.25, h: 0.8, fontFace: F.body, fontSize: 12, color: C.muted, lineSpacing: 17, isTextBox: true, margin: 0 });
  });
  s.addText("Проверено тестами: изоляция базы, коды ошибок, отсутствие ФИО в интеграционной выгрузке.", {
    x: M, y: 6.4, w: W - 2 * M, h: 0.4, fontFace: F.body, fontSize: 12, italic: true, color: C.muted, isTextBox: true, margin: 0,
  });
  s.addNotes("152-ФЗ выполняется не декларацией, а тем, что личных данных в системе просто нет.");
}

/* --- 14. итог ----------------------------------------------------------- */
{
  const s = darkSlide();
  s.addText("ЧТО ГОТОВО И ЧТО ДАЛЬШЕ", { x: M, y: 0.5, w: 8, h: 0.3, fontFace: F.body, fontSize: 11, bold: true, color: C.red, charSpacing: 1.6, isTextBox: true, margin: 0 });
  s.addText("Рабочий прототип, а не макет", { x: M, y: 0.85, w: W - 2 * M, h: 0.8, fontFace: F.head, fontSize: 32, bold: true, color: C.white, isTextBox: true, margin: 0 });

  const ready = [
    "6 сценариев и 2 рейса на данных кейса",
    "Таймеры, две шкалы, память между инцидентами",
    "Разбор с причинами, альтернативами и выводами",
    "Профиль, достижения, рейтинг, рейс недели, серии",
    "API с OpenAPI, интеграции с HR и LMS по токену",
    "33 теста, валидатор контента, запуск одной командой",
  ];
  const next = [
    "Веб-редактор сценариев для методистов",
    "Остальные ситуации методички по данным аналитики",
    "SSO и профиль из HR, назначение обучения из LMS",
    "Свободная реплика вместо выбора варианта: исход считает то же ядро",
    "Роль инструктора и разбор партии с наставником",
  ];

  s.addShape(pres.ShapeType.roundRect, { x: M, y: 1.9, w: 5.85, h: 3.4, rectRadius: 0.14, fill: { color: C.inkSoft }, line: { color: C.line, width: 1 } });
  s.addText("Сделано", { x: M + 0.3, y: 2.1, w: 5, h: 0.4, fontFace: F.head, fontSize: 18, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText(
    ready.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < ready.length - 1 } })),
    { x: M + 0.3, y: 2.6, w: 5.25, h: 3.1, valign: "top", fontFace: F.body, fontSize: 12.5, color: C.mutedDark, paraSpaceAfter: 8, isTextBox: true, margin: 0 }
  );

  s.addShape(pres.ShapeType.roundRect, { x: 6.85, y: 1.9, w: 5.8, h: 3.4, rectRadius: 0.14, fill: { color: C.inkSoft }, line: { color: C.line, width: 1 } });
  s.addText("План развития", { x: 7.15, y: 2.1, w: 5, h: 0.4, fontFace: F.head, fontSize: 18, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText(
    next.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < next.length - 1 } })),
    { x: 7.15, y: 2.6, w: 5.2, h: 3.1, valign: "top", fontFace: F.body, fontSize: 12.5, color: C.mutedDark, paraSpaceAfter: 8, isTextBox: true, margin: 0 }
  );

  s.addText("Репозиторий, инструкция запуска и пакет документации — в README проекта.", {
    x: M, y: 5.6, w: 11.9, h: 0.4, fontFace: F.body, fontSize: 13, color: C.white, isTextBox: true, margin: 0,
  });
  s.addNotes("Финал: подчёркиваем, что решение управляемое — сценарий добавляется без программиста, и всё запускается одной командой.");
}

pres.writeFile({ fileName: path.join(__dirname, "peregon.pptx") }).then((f) => console.log("written", f));
