/* Презентация проекта «Перегон» в фирменном шаблоне хакатона Московского транспорта.
   Фон-паттерн, логотипы и заголовочный знак взяты из официального шаблона
   (ресурсы/Презентация МТТЕХ.pptx), холст и палитра — оттуда же. */
const pptxgen = require("pptxgenjs");
const path = require("path");

const SHOTS = path.join(__dirname, "shots");
const TPL = path.join(__dirname, "template");   // ассеты из официального шаблона МТТЕХ
const shot = (name) => path.join(SHOTS, name);

// Ассеты шаблона
const BG_DARK = path.join(TPL, "bg-dark.png");   // паттерн транспорта на тёмном
const BG_BLUE = path.join(TPL, "bg-blue.png");   // синий градиент
const LOGOS = path.join(TPL, "logos.png");       // МТТЕХ + Транспортные инновации Москвы
const WORDMARK = path.join(TPL, "wordmark.png"); // «Хакатон Московского транспорта»

const C = {
  navy: "1A1230",
  blue: "3F6FD1",
  blueDeep: "2B4FA0",
  body: "9FC5E8",
  white: "FFFFFF",
  dim: "6F7AA8",
  green: "35C17A",
  amber: "E0A63C",
  red: "E0384E",
};

const F = "Arial"; // шаблон свёрстан на Google Sans; Arial — безопасная замена

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 × 5.625 — как в шаблоне
pres.author = "Команда проекта «Перегон»";
pres.title = "Перегон — тренажёр проводника ВСМ";

const W = 10;
const H = 5.625;
const M = 0.55;

/* --- каркас слайдов ----------------------------------------------------- */

function logos(s, { y = H - 0.55 } = {}) {
  s.addImage({ path: LOGOS, x: W - 2.35, y, w: 1.78, h: 0.27 });
}

function steps(s, { x, y, size = 0.3, color = C.blue }) {
  // Фирменный мотив шаблона: смещённые квадраты «лесенкой».
  s.addShape(pres.ShapeType.rect, { x, y, w: size, h: size, fill: { color } });
  s.addShape(pres.ShapeType.rect, { x: x + size, y: y + size, w: size, h: size, fill: { color } });
  s.addShape(pres.ShapeType.rect, { x: x + 2 * size, y, w: size, h: size, fill: { color: C.blueDeep } });
}

function darkSlide({ title, sub, motif = true } = {}) {
  const s = pres.addSlide();
  s.background = { color: C.navy };
  s.addImage({ path: BG_DARK, x: 0, y: 0, w: W, h: H });
  if (title) {
    s.addText(title, {
      x: M, y: 0.34, w: W - 2 * M - 1.2, h: 0.62,
      fontFace: F, fontSize: 26, bold: true, color: C.white, valign: "top", isTextBox: true, margin: 0,
    });
  }
  if (sub) {
    s.addText(sub, {
      x: M, y: 1.02, w: W - 2 * M - 1.0, h: 0.5,
      fontFace: F, fontSize: 12, color: C.body, lineSpacing: 17, valign: "top", isTextBox: true, margin: 0,
    });
  }
  if (motif) steps(s, { x: W - 1.35, y: 0.34, size: 0.26 });
  logos(s);
  return s;
}

function blueSlide({ title, sub } = {}) {
  const s = pres.addSlide();
  s.background = { color: C.blueDeep };
  s.addImage({ path: BG_BLUE, x: 0, y: 0, w: W, h: H });
  if (title) {
    s.addText(title, {
      x: M, y: 0.34, w: W - 2 * M - 1.3, h: 0.62,
      fontFace: F, fontSize: 26, bold: true, color: C.white, valign: "top", isTextBox: true, margin: 0,
    });
  }
  if (sub) {
    s.addText(sub, {
      x: M, y: 1.02, w: W - 2 * M - 1.0, h: 0.5,
      fontFace: F, fontSize: 12, color: "DDE8FA", lineSpacing: 17, valign: "top", isTextBox: true, margin: 0,
    });
  }
  steps(s, { x: W - 1.35, y: 0.34, size: 0.26, color: C.white });
  logos(s);
  return s;
}

function dividerSlide(text) {
  // Слайд-разделитель шаблона: синяя плашка на весь экран, белая полоса с темой.
  const s = pres.addSlide();
  s.background = { color: C.blue };
  s.addShape(pres.ShapeType.rect, { x: 0.28, y: 4.1, w: W - 0.56, h: 0.95, fill: { color: C.white } });
  s.addText(text, {
    x: 0.55, y: 4.1, w: W - 1.1, h: 0.95, valign: "middle",
    fontFace: F, fontSize: 26, bold: true, color: C.navy, isTextBox: true, margin: 0,
  });
  return s;
}

function card(s, { x, y, w, h, fill = "231A3E", line = "39305C" }) {
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: fill }, line: { color: line, width: 1 } });
}

function blueCard(s, { x, y, w, h }) {
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: C.blue } });
}

function cardText(s, { x, y, w, title, body, titleColor = C.white, bodyColor = C.body, titleSize = 12.5, bodySize = 9.5 }) {
  s.addText(title, {
    x, y, w, h: 0.24, valign: "top", fontFace: F, fontSize: titleSize, bold: true, color: titleColor,
    isTextBox: true, margin: 0,
  });
  s.addText(body, {
    x, y: y + 0.26, w, h: 0.75, valign: "top", fontFace: F, fontSize: bodySize, color: bodyColor,
    lineSpacing: 12.5, isTextBox: true, margin: 0,
  });
}

/* --- 1. титул ----------------------------------------------------------- */
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  s.addImage({ path: BG_DARK, x: 0, y: 0, w: W, h: H });
  s.addImage({ path: LOGOS, x: W - 2.75, y: 0.36, w: 2.0, h: 0.3 });
  s.addImage({ path: WORDMARK, x: 0.5, y: 0.85, w: 5.4, h: 1.73 });
  s.addText("Перегон", {
    x: 0.62, y: 2.7, w: 6, h: 0.75,
    fontFace: F, fontSize: 40, bold: true, color: C.white, isTextBox: true, margin: 0,
  });
  s.addText("геймифицированный тренажёр проводника высокоскоростной магистрали", {
    x: 0.63, y: 3.45, w: 6.6, h: 0.4,
    fontFace: F, fontSize: 12, color: C.body, isTextBox: true, margin: 0,
  });
  s.addText("Трек «Геймификация для ВСМ»", {
    x: 0.63, y: 3.9, w: 6, h: 0.3,
    fontFace: F, fontSize: 11, color: C.dim, isTextBox: true, margin: 0,
  });
  ["6 сценариев", "2 рейса по 3 инцидента", "53 узла · 92 варианта", "33 теста"].forEach((t, i) => {
    const x = 0.62 + (i % 2) * 2.35;
    const y = 4.35 + Math.floor(i / 2) * 0.45;
    s.addShape(pres.ShapeType.rect, { x, y, w: 2.2, h: 0.36, fill: { color: "231A3E" }, line: { color: "39305C", width: 1 } });
    s.addText(t, {
      x, y, w: 2.2, h: 0.36, align: "center", valign: "middle",
      fontFace: F, fontSize: 10, color: C.white, isTextBox: true, margin: 0,
    });
  });
  steps(s, { x: 7.7, y: 4.35, size: 0.34 });
  s.addNotes(
    "Мы сделали тренажёр, где проводник ВСМ проживает нештатные ситуации целым рейсом, " +
    "а не отвечает на вопросы теста. Покажу три механики, которых нет в квизе с таймером."
  );
}

/* --- 2. проблема -------------------------------------------------------- */
{
  const s = darkSlide({
    title: "Тест проверяет знание регламента",
    sub: "Он не проверяет, вспомнит ли проводник это знание, когда в вагоне на 400 км/ч\nодновременно плачет ребёнок, пассажиру плохо и до станции семь минут.",
  });
  const items = [
    ["Стресс и дефицит времени", "Решение принимается за секунды. Лекция и тест этому не учат: там можно подумать и перечитать."],
    ["Нет безопасной среды", "Отрабатывать конфликт или медицинский инцидент на реальных пассажирах нельзя."],
    ["Soft skills не измеряются", "«Умеет успокоить пассажира» — не галочка в тесте. Нужна оценка, понятная сотруднику и методисту."],
  ];
  items.forEach(([t, b], i) => {
    const x = M + i * 3.05;
    card(s, { x, y: 1.95, w: 2.85, h: 1.95 });
    s.addShape(pres.ShapeType.rect, { x: x + 0.22, y: 2.17, w: 0.16, h: 0.16, fill: { color: C.blue } });
    cardText(s, { x: x + 0.22, y: 2.45, w: 2.4, title: t, body: b });
  });
  s.addText(
    "Данные кейса: методичка «Примеры ситуаций взаимодействия поездного персонала с пассажирами» —\n" +
    "51 ситуация с эталонными реакциями; стандарты СТО РЖД по обслуживанию пассажиров ВСМ.",
    { x: M, y: 4.25, w: 7.5, h: 0.6, fontFace: F, fontSize: 9.5, italic: true, color: C.dim, lineSpacing: 13, isTextBox: true, margin: 0 }
  );
  s.addNotes("Проводник знает регламент. Вопрос в том, вспомнит ли он его под давлением.");
}

/* --- 3. разделитель ----------------------------------------------------- */
{
  const s = dividerSlide("Решение");
  s.addNotes("Переходим к тому, что именно мы построили.");
}

/* --- 4. идея ------------------------------------------------------------ */
{
  const s = darkSlide({
    title: "Тренировка — это рейс, а не набор вопросов",
    sub: "Смена проводника: несколько нештатных ситуаций подряд на маршруте Москва — Санкт-Петербург.\nШкалы не обнуляются между инцидентами, а пассажиры помнят прошлый перегон.",
  });
  const tiles = [
    ["Таймер от маршрута", "Медиков вызывают к платформе, пассажира передают полиции на вокзале. Не успел до станции — вариант закрылся.", C.amber],
    ["Две шкалы", "«Лояльность пассажира» и «рейтинг безопасности» тянут в разные стороны. Безопасность не торгуется.", C.blue],
    ["Память пассажиров", "Салон, с которым нашли общий язык, помогает. Видевший публичный спор — достаёт телефон.", C.green],
    ["Разбор со ссылкой", "Каждый балл объяснён причиной и пунктом методички. Плюс ветка, которую вы не выбрали.", C.red],
  ];
  tiles.forEach(([t, b, color], i) => {
    const x = M + i * 2.28;
    card(s, { x, y: 1.95, w: 2.1, h: 2.35 });
    s.addShape(pres.ShapeType.rect, { x: x + 0.2, y: 2.15, w: 0.16, h: 0.16, fill: { color } });
    cardText(s, { x: x + 0.2, y: 2.42, w: 1.72, title: t, body: b, titleSize: 11.5, bodySize: 9 });
  });
  s.addText("Всё это — данные, а не код: методист добавляет ситуацию из методички без программиста.", {
    x: M, y: 4.5, w: 7.6, h: 0.3, fontFace: F, fontSize: 10.5, color: C.white, isTextBox: true, margin: 0,
  });
  s.addNotes("Ключевая мысль: рейс, а не квиз. Лояльность здесь — ресурс, который работает дальше по смене.");
}

/* --- 5. интерфейс ------------------------------------------------------- */
{
  const s = darkSlide({ title: "Инцидент подаётся как лайт-новелла" });
  s.addImage({ path: shot("02-novel.png"), x: M, y: 1.15, w: 5.5, h: 3.85, sizing: { type: "contain", w: 5.5, h: 3.85 } });
  const notes = [
    ["Сцена и персонаж", "Фон вагона и собеседник со сменой эмоции: спокоен → доволен → напряжён → на взводе."],
    ["Обе шкалы сверху", "Последствие решения видно сразу, а не только в конце."],
    ["Таймер от сервера", "Браузер не передаёт время: момент показа узла лежит в базе."],
    ["Шаг ролевой модели", "У каждого варианта подписан шаг: признать → правило → решение → заверить."],
  ];
  notes.forEach(([t, b], i) => {
    const y = 1.2 + i * 0.97;
    s.addShape(pres.ShapeType.rect, { x: 6.25, y: y + 0.04, w: 0.14, h: 0.14, fill: { color: C.blue } });
    cardText(s, { x: 6.5, y, w: 2.95, title: t, body: b, titleSize: 11.5, bodySize: 9 });
  });
  s.addNotes("Арт подключается файлами, без кода. Режим новеллы включается для сценариев со сценой.");
}

/* --- 6. движок ---------------------------------------------------------- */
{
  const s = darkSlide({ title: "Сценарий — это данные, а не код" });
  card(s, { x: M, y: 1.2, w: 5.1, h: 3.5, fill: "120C24", line: "2C2350" });
  const yaml = [
    "options:",
    "  - id: radio",
    "    step: solution          # шаг ролевой модели",
    "    text: «Вызвать начальника поезда и попросить",
    "           медиков к платформе в Твери»",
    "    reason: Штатный порядок вызова медиков",
    "            (методичка, ситуация 19)",
    "    effects:",
    "      loyalty: 6",
    "      safety: 15",
    "      competences: {safety: 3, teamwork: 3}",
    "      set: [medics_called]  # память рейса",
    "    goto_if:",
    "      - flag: car_tense     # вагон помнит спор",
    "        goto: filmed",
    "    goto: care",
  ].join("\n");
  s.addText(yaml, {
    x: M + 0.18, y: 1.35, w: 4.8, h: 3.2,
    fontFace: "Courier New", fontSize: 8, color: "CBD9F2", lineSpacing: 11.5, isTextBox: true, margin: 0,
  });
  const stats = [
    ["6", "сценариев из методички"],
    ["53", "узла, 92 варианта"],
    ["2", "рейса по три инцидента"],
    ["12", "достижений"],
  ];
  stats.forEach(([v, l], i) => {
    const x = 6.0 + (i % 2) * 1.85;
    const y = 1.2 + Math.floor(i / 2) * 1.05;
    s.addText(v, { x, y, w: 1.7, h: 0.5, fontFace: F, fontSize: 28, bold: true, color: C.blue, isTextBox: true, margin: 0 });
    s.addText(l, { x, y: y + 0.5, w: 1.7, h: 0.4, fontFace: F, fontSize: 9, color: C.body, lineSpacing: 12, isTextBox: true, margin: 0 });
  });
  s.addText(
    "Загрузчик проверяет файл целиком: битая ссылка между узлами, таймер без ветки «время вышло», " +
    "недостижимый узел — ошибка при старте, а не в середине партии. Валидатор для методиста ловит " +
    "варианты без объяснения.",
    { x: 6.0, y: 3.4, w: 3.45, h: 1.3, fontFace: F, fontSize: 9, color: C.body, lineSpacing: 12.5, isTextBox: true, margin: 0 }
  );
  s.addNotes("Здесь показываем правку вживую: поменять цену решения, запустить validate.py, перезапустить бэкенд.");
}

/* --- 7. ролевая модель -------------------------------------------------- */
{
  const s = darkSlide({
    title: "Важно не только что сказано, но и в каком порядке",
    sub: "Ролевая модель из методички кейса реализована как механика начисления, а не как справка.",
  });
  const chain = ["Признать\nситуацию", "Обозначить\nправило", "Предложить\nрешение", "Заверить"];
  chain.forEach((t, i) => {
    const x = M + i * 2.25;
    blueCard(s, { x, y: 1.75, w: 1.95, h: 0.75 });
    s.addText(t, {
      x, y: 1.75, w: 1.95, h: 0.75, align: "center", valign: "middle",
      fontFace: F, fontSize: 10.5, bold: true, color: C.white, isTextBox: true, margin: 0,
    });
    if (i < 3) {
      s.addText("→", { x: x + 1.95, y: 1.75, w: 0.3, h: 0.75, align: "center", valign: "middle", fontFace: F, fontSize: 14, color: C.blue, isTextBox: true, margin: 0 });
    }
  });

  card(s, { x: M, y: 2.75, w: 4.35, h: 1.75 });
  s.addText("Правило до признания", { x: M + 0.2, y: 2.92, w: 3.9, h: 0.3, fontFace: F, fontSize: 12.5, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText("«Вы пьяны, алкоголь я вам не принесу»", { x: M + 0.2, y: 3.22, w: 3.9, h: 0.3, fontFace: F, fontSize: 10, italic: true, color: C.body, isTextBox: true, margin: 0 });
  s.addText("−4 лояльности сверх эффекта самой реплики", { x: M + 0.2, y: 3.55, w: 3.9, h: 0.3, fontFace: F, fontSize: 11, bold: true, color: C.red, isTextBox: true, margin: 0 });
  s.addText("Методичка запрещает называть состояние пассажира вслух: это провоцирует агрессию.", { x: M + 0.2, y: 3.86, w: 3.9, h: 0.5, fontFace: F, fontSize: 9, color: C.body, lineSpacing: 12, isTextBox: true, margin: 0 });

  card(s, { x: 5.1, y: 2.75, w: 4.35, h: 1.75 });
  s.addText("Решение после признания", { x: 5.3, y: 2.92, w: 3.9, h: 0.3, fontFace: F, fontSize: 12.5, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText("«Этот напиток предложить не могу. Позвольте чай или кофе?»", { x: 5.3, y: 3.22, w: 3.9, h: 0.3, fontFace: F, fontSize: 10, italic: true, color: C.body, isTextBox: true, margin: 0 });
  s.addText("+3 лояльности и +1 к компетенции «сервис»", { x: 5.3, y: 3.55, w: 3.9, h: 0.3, fontFace: F, fontSize: 11, bold: true, color: C.green, isTextBox: true, margin: 0 });
  s.addText("Движок сравнивает шаг текущего хода с предыдущим — отдельно от эффектов реплики.", { x: 5.3, y: 3.86, w: 3.9, h: 0.5, fontFace: F, fontSize: 9, color: C.body, lineSpacing: 12, isTextBox: true, margin: 0 });

  s.addText("Правила лежат списком в engine.SEQUENCE_RULES — меняются за минуту.", {
    x: M, y: 4.62, w: 7.5, h: 0.3, fontFace: F, fontSize: 9.5, italic: true, color: C.dim, isTextBox: true, margin: 0,
  });
  s.addNotes("Это прямая реализация ролевой модели из методички: четыре шага со страницы 2.");
}

/* --- 8. память рейса ---------------------------------------------------- */
{
  const s = darkSlide({
    title: "Пассажиры помнят прошлый перегон",
    sub: "Шкалы и флаги переезжают из инцидента в инцидент — это и есть память рейса.",
  });
  const chain = [
    ["Инцидент 1", "Два пассажира на одно место"],
    ["Инцидент 2", "Ребёнок потерялся"],
    ["Инцидент 3", "Пассажиру стало плохо"],
  ];
  chain.forEach(([n, t], i) => {
    const x = M + i * 3.05;
    card(s, { x, y: 1.75, w: 2.75, h: 0.8 });
    s.addText(n, { x: x + 0.18, y: 1.85, w: 2.4, h: 0.22, fontFace: F, fontSize: 8.5, color: C.dim, isTextBox: true, margin: 0 });
    s.addText(t, { x: x + 0.18, y: 2.07, w: 2.4, h: 0.4, fontFace: F, fontSize: 11, bold: true, color: C.white, isTextBox: true, margin: 0 });
    if (i < 2) {
      s.addText("→", { x: x + 2.75, y: 1.75, w: 0.3, h: 0.8, align: "center", valign: "middle", fontFace: F, fontSize: 14, color: C.blue, isTextBox: true, margin: 0 });
    }
  });

  card(s, { x: M, y: 2.8, w: 4.35, h: 1.65, fill: "14301F", line: "2F6B46" });
  s.addText("Спор решён по-человечески", { x: M + 0.2, y: 2.97, w: 3.9, h: 0.3, fontFace: F, fontSize: 12, bold: true, color: C.green, isTextBox: true, margin: 0 });
  s.addText(
    "В медицинском инциденте открывается вариант «попросить пассажиров, с которыми вы уже нашли общий язык, помочь». " +
    "Лояльность перестаёт быть баллом и становится ресурсом.",
    { x: M + 0.2, y: 3.3, w: 3.9, h: 1.0, fontFace: F, fontSize: 9.5, color: "D6EFE0", lineSpacing: 13, isTextBox: true, margin: 0 }
  );

  card(s, { x: 5.1, y: 2.8, w: 4.35, h: 1.65, fill: "33141C", line: "7A2B3A" });
  s.addText("Был публичный спор в салоне", { x: 5.3, y: 2.97, w: 3.9, h: 0.3, fontFace: F, fontSize: 12, bold: true, color: "FF8A9B", isTextBox: true, margin: 0 });
  s.addText(
    "Тот же ход ведёт в другой узел: сосед через проход поднимает телефон и снимает пассажирку, которой плохо. " +
    "Появляется развилка про согласие на съёмку.",
    { x: 5.3, y: 3.3, w: 3.9, h: 1.0, fontFace: F, fontSize: 9.5, color: "F5D8DE", lineSpacing: 13, isTextBox: true, margin: 0 }
  );

  s.addText("В данных это две строчки: requires: [goodwill_car] и goto_if: [{flag: car_tense, goto: filmed}].", {
    x: M, y: 4.58, w: 8.5, h: 0.3, fontFace: F, fontSize: 9, italic: true, color: C.dim, isTextBox: true, margin: 0,
  });
  s.addNotes("На демонстрации показываем экран перехода между инцидентами с плашкой «Память рейса».");
}

/* --- 9. время (синий) --------------------------------------------------- */
{
  const s = blueSlide({
    title: "Таймер задаёт не игра, а маршрут",
    sub: "Поезд на 400 км/ч не остановится по требованию: всё, что делается через станцию, нужно решить до неё.",
  });
  const blocks = [
    ["Окно закрывается", "Чем дольше тянешь, тем меньше мягких вариантов: часть решений исчезает из списка."],
    ["Бездействие — выбор", "Истёк таймер — своя ветка: ситуация развивается сама, хладнокровие падает, минус три балла к итогу."],
    ["Время считает сервер", "В базе лежит момент показа узла. Браузер не передаёт длительность — «подкрутить» таймер нельзя."],
    ["Быстро ≠ наугад", "Верное решение в первой половине таймера даёт +2 к хладнокровию, на исходе — минус один."],
  ];
  blocks.forEach(([t, b], i) => {
    const x = M + (i % 2) * 4.55;
    const y = 2.0 + Math.floor(i / 2) * 1.32;
    s.addShape(pres.ShapeType.rect, { x, y, w: 4.35, h: 1.12, fill: { color: "1E3A78" }, line: { color: "3F6FD1", width: 1 } });
    s.addText(t, { x: x + 0.2, y: y + 0.14, w: 3.95, h: 0.3, fontFace: F, fontSize: 12, bold: true, color: C.white, isTextBox: true, margin: 0 });
    s.addText(b, { x: x + 0.2, y: y + 0.45, w: 3.95, h: 0.6, fontFace: F, fontSize: 9.5, color: "DDE8FA", lineSpacing: 12.5, isTextBox: true, margin: 0 });
  });
  s.addText("Честный таймер — обязательное условие честной таблицы лидеров.", {
    x: M, y: 4.75, w: 7.5, h: 0.3, fontFace: F, fontSize: 10.5, color: C.white, isTextBox: true, margin: 0,
  });
  s.addNotes("На демонстрации специально даём таймеру истечь: ситуация уходит в другую ветку, видно на шкалах.");
}

/* --- 10. разбор --------------------------------------------------------- */
{
  const s = darkSlide({ title: "Не «верно / неверно», а объяснение" });
  s.addImage({ path: shot("06-debrief-events.png"), x: 5.15, y: 1.15, w: 4.3, h: 3.6, sizing: { type: "contain", w: 4.3, h: 3.6 } });
  const items = [
    ["Причина у каждого балла", "Со ссылкой на ситуацию из методички и стандарт обслуживания."],
    ["Как можно было лучше", "У слабых вариантов — прямая подсказка, что стоило сделать вместо этого."],
    ["Что было бы, если", "Движок показывает невыбранную ветку, но только когда она была заметно лучше."],
    ["Выводы о человеке", "«Безопасность просела: сначала риск, потом сервис» — и подбор следующих рейсов."],
  ];
  items.forEach(([t, b], i) => {
    const y = 1.2 + i * 0.92;
    s.addShape(pres.ShapeType.rect, { x: M, y: y + 0.04, w: 0.14, h: 0.14, fill: { color: C.blue } });
    cardText(s, { x: M + 0.26, y, w: 4.1, title: t, body: b, titleSize: 11.5, bodySize: 9 });
  });
  s.addNotes("Главный учебный момент: не оценка, а объяснение с нормативной основой.");
}

/* --- 11. геймификация --------------------------------------------------- */
{
  const s = darkSlide({ title: "Цикл: действие → очки → достижения → рейтинг" });
  s.addImage({ path: shot("07-profile.png"), x: M, y: 1.15, w: 4.3, h: 2.55, sizing: { type: "contain", w: 4.3, h: 2.55 } });
  s.addImage({ path: shot("08-leaderboard.png"), x: 5.15, y: 1.15, w: 4.3, h: 2.55, sizing: { type: "contain", w: 4.3, h: 2.55 } });
  const items = [
    ["Профиль", "Пять компетенций, пять уровней: стажёр → наставник."],
    ["Достижения", "За поведение: «Холодная голова» — десять решений вовремя."],
    ["Рейс недели", "Один сценарий для всех бригад — сравнение честное."],
    ["Серии и баллы", "Дни подряд, сгорающие очки, уведомления о назначениях."],
  ];
  items.forEach(([t, b], i) => {
    const x = M + i * 2.28;
    cardText(s, { x, y: 3.95, w: 2.1, title: t, body: b, titleSize: 11, bodySize: 8.5 });
  });
  s.addNotes("Рейтинг честен, потому что ядро детерминированное, а время считает сервер.");
}

/* --- 12. аналитика ------------------------------------------------------ */
{
  const s = darkSlide({
    title: "Данные о реальных пробелах в подготовке",
    sub: "Каждый ход пишется в журнал: узел, выбор, время, изменения шкал и причина.",
  });
  s.addImage({ path: shot("09-analytics.png"), x: 5.0, y: 1.6, w: 4.45, h: 3.1, sizing: { type: "contain", w: 4.45, h: 3.1 } });
  const items = [
    ["Где ошибаются чаще всего", "Развилки с наибольшей потерей шкал по всем прохождениям: видно не «кто плохой», а какая тема не отработана."],
    ["Динамика компетенций", "Сравнение первой и второй половины рейсов сотрудника: что выросло, а что стоит на месте."],
  ];
  items.forEach(([t, b], i) => {
    const y = 1.75 + i * 1.35;
    card(s, { x: M, y, w: 4.2, h: 1.15 });
    cardText(s, { x: M + 0.2, y: y + 0.15, w: 3.8, title: t, body: b, titleSize: 11.5, bodySize: 9 });
  });
  s.addText("Те же данные уходят в HR и LMS через документированный API.", {
    x: M, y: 4.55, w: 4.3, h: 0.3, fontFace: F, fontSize: 9.5, italic: true, color: C.dim, isTextBox: true, margin: 0,
  });
  s.addNotes("Для заказчика главный аргумент: тренажёр показывает, чему учить дальше.");
}

/* --- 13. разделитель ---------------------------------------------------- */
{
  dividerSlide("Как это устроено").addNotes("Переходим к архитектуре и требованиям кейса.");
}

/* --- 14. архитектура ---------------------------------------------------- */
{
  const s = darkSlide({ title: "Модульно, без «чёрных ящиков»" });
  s.addImage({ path: path.join(__dirname, "arch.png"), x: M, y: 1.1, w: 6.0, h: 3.7, sizing: { type: "contain", w: 6.0, h: 3.7 } });
  const items = [
    ["Стек", "Frontend без сборки (HTML/CSS/JS), backend на FastAPI, хранилище SQLite."],
    ["Ядро отдельно", "engine.py не знает ни про HTTP, ни про БД: партия воспроизводится в тесте одной функцией."],
    ["API", "OpenAPI на /docs; интеграции с HR и LMS — по токену X-API-Key."],
    ["Запуск", "Python 3.11 и одна команда. Есть Dockerfile и compose."],
  ];
  items.forEach(([t, b], i) => {
    const y = 1.2 + i * 0.92;
    cardText(s, { x: 6.75, y, w: 2.7, title: t, body: b, titleSize: 11, bodySize: 8.5 });
  });
  s.addNotes("Состояние партии в БД, поэтому бэкенд масштабируется без липких сессий.");
}

/* --- 15. безопасность --------------------------------------------------- */
{
  const s = darkSlide({
    title: "Демо-среда без персональных данных",
    sub: "152-ФЗ выполняется не декларацией, а тем, что личных данных в системе просто нет.",
  });
  const items = [
    ["Только синтетика", "Профили, бригады и депо придуманы. Пассажиры — персонажи: ни имён из жизни, ни номеров билетов.", C.green],
    ["Минимизация в выгрузке", "В HR уходят логин, подразделение и учебные показатели. ФИО тренажёру не нужно и не хранится.", C.blue],
    ["Секретов в коде нет", "Токен интеграции лежит в базе и выдаётся администратором; база создаётся локально.", C.amber],
    ["Предсказуемые ошибки", "404 / 409 / 422 / 401, а битая ссылка в сценарии — ошибка при загрузке, а не в партии.", C.red],
  ];
  items.forEach(([t, b, color], i) => {
    const x = M + (i % 2) * 4.55;
    const y = 1.95 + Math.floor(i / 2) * 1.3;
    card(s, { x, y, w: 4.35, h: 1.12 });
    s.addShape(pres.ShapeType.rect, { x: x + 0.2, y: y + 0.16, w: 0.14, h: 0.14, fill: { color } });
    cardText(s, { x: x + 0.2, y: y + 0.38, w: 3.95, title: t, body: b, titleSize: 11.5, bodySize: 9 });
  });
  s.addText("Проверено тестами: изоляция базы, коды ошибок, отсутствие ФИО в интеграционной выгрузке.", {
    x: M, y: 4.7, w: 8, h: 0.3, fontFace: F, fontSize: 9.5, italic: true, color: C.dim, isTextBox: true, margin: 0,
  });
  s.addNotes("Персональных данных нет ни в демо, ни в выгрузке — это требование кейса.");
}

/* --- 16. итоги ---------------------------------------------------------- */
{
  const s = darkSlide({ title: "Рабочий прототип, а не макет" });
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
    "Свободная реплика: распознаём ход, исход считает ядро",
    "Роль инструктора и разбор партии с наставником",
  ];
  card(s, { x: M, y: 1.15, w: 4.35, h: 2.55 });
  s.addText("Сделано", { x: M + 0.22, y: 1.3, w: 3.9, h: 0.3, fontFace: F, fontSize: 14, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText(
    ready.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < ready.length - 1 } })),
    { x: M + 0.22, y: 1.65, w: 3.95, h: 2.4, valign: "top", fontFace: F, fontSize: 9.5, color: C.body, paraSpaceAfter: 6, isTextBox: true, margin: 0 }
  );

  card(s, { x: 5.1, y: 1.15, w: 4.35, h: 2.55 });
  s.addText("План развития", { x: 5.32, y: 1.3, w: 3.9, h: 0.3, fontFace: F, fontSize: 14, bold: true, color: C.white, isTextBox: true, margin: 0 });
  s.addText(
    next.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < next.length - 1 } })),
    { x: 5.32, y: 1.65, w: 3.95, h: 2.4, valign: "top", fontFace: F, fontSize: 9.5, color: C.body, paraSpaceAfter: 6, isTextBox: true, margin: 0 }
  );

  s.addText("Запуск у заказчика — три строки и только Python 3.11:", {
    x: M, y: 3.95, w: 8.9, h: 0.28, fontFace: F, fontSize: 11, color: C.white, isTextBox: true, margin: 0,
  });
  s.addShape(pres.ShapeType.rect, { x: M, y: 4.28, w: 8.9, h: 0.72, fill: { color: "120C24" }, line: { color: "2C2350", width: 1 } });
  s.addText([
    "git clone <репозиторий> vsm-trainer",
    "cd vsm-trainer",
    "python run.py",
  ].join("\n"), {
    x: M + 0.18, y: 4.34, w: 8.5, h: 0.6, valign: "top",
    fontFace: "Courier New", fontSize: 9, color: "CBD9F2", lineSpacing: 11, isTextBox: true, margin: 0,
  });
  s.addText("Окружение, зависимости и демо-данные скрипт делает сам. Документация — в README.", {
    x: M, y: 5.05, w: 7.5, h: 0.28, fontFace: F, fontSize: 9, color: C.dim, isTextBox: true, margin: 0,
  });
  s.addNotes("Финал: решение управляемое — сценарий добавляется без программиста, запуск одной командой.");
}

pres.writeFile({ fileName: path.join(__dirname, "peregon.pptx") }).then((f) => console.log("written", f));
