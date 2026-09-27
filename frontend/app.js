/* Фронтенд тренажёра: вся игровая логика на сервере, здесь — экраны и таймер.
   Таймер в браузере только рисуется: истечение времени подтверждает сервер
   по своим часам, поэтому «подкрутить» его из консоли нельзя. */

const API = "/api/v1";
const state = {
  login: localStorage.getItem("vsm_login") || "a.smirnova",
  view: "catalog",
  run: null,
  timer: null,
  reference: { competences: {}, steps: {} },
  novel: localStorage.getItem("vsm_novel") !== "off",   // лайт-новелла включена по умолчанию
  typing: null,
};

const app = document.getElementById("app");

async function api(path, options = {}) {
  const response = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(detail.detail || "ошибка запроса");
  }
  return response.json();
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function scales(loyalty, safety, deltas = {}) {
  const mark = (value) =>
    value ? `<span class="delta ${value > 0 ? "up" : "down"}">${value > 0 ? "+" : ""}${value}</span>` : "";
  return `
    <div class="scales">
      <div class="scale">
        <div class="label"><span>Лояльность пассажира ${mark(deltas.loyalty)}</span><b>${loyalty}</b></div>
        <div class="bar loyal"><i style="width:${loyalty}%"></i></div>
      </div>
      <div class="scale">
        <div class="label"><span>Рейтинг безопасности ${mark(deltas.safety)}</span><b>${safety}</b></div>
        <div class="bar safe"><i style="width:${safety}%"></i></div>
      </div>
    </div>`;
}

/* --- каталог рейсов --- */

async function viewCatalog() {
  const [trips, scenarios, challenge, streak] = await Promise.all([
    api("/trips"),
    api(`/scenarios?login=${encodeURIComponent(state.login)}`),
    api(`/challenge?login=${encodeURIComponent(state.login)}`),
    api(`/conductors/${encodeURIComponent(state.login)}/streak`),
  ]);

  const expiring = streak.expiring;
  app.innerHTML = `
    <div class="card challenge">
      <div class="row spread">
        <h3>🏁 Рейс недели · ${challenge.week}</h3>
        <span class="meta">${challenge.played ? "вы уже прошли" : `бонус ${challenge.bonus_xp} очков`}</span>
      </div>
      <div class="meta">Один и тот же сценарий для всех бригад — сравнение честное.</div>
      <p><b>${challenge.scenario.title}</b><br><span class="meta">${challenge.scenario.summary}</span></p>
      <div class="row spread">
        <span class="meta">🔥 Серия: ${streak.streak_days} дн.${
          expiring.days_left !== null && expiring.points
            ? ` · ${expiring.points} очков челленджа сгорят через ${expiring.days_left} дн.`
            : ""
        }</span>
        <button class="primary" data-challenge="${challenge.scenario.id}">Пройти рейс недели</button>
      </div>
    </div>

    <div class="card"><h3>Рейсы смены</h3>
      <div class="meta">Несколько инцидентов подряд: шкалы не обнуляются, а пассажиры
      помнят, как вы с ними обошлись на прошлом перегоне.</div>
    </div>
    ${trips
      .map(
        (t) => `
      <div class="card trip">
        <div class="row spread">
          <h3>${t.title}</h3>
          <span class="meta">${"★".repeat(t.difficulty)}</span>
        </div>
        <div class="meta">${t.route}</div>
        <p>${t.summary}</p>
        <div class="chain">
          ${t.segments.map((s, i) => `<span class="link">${i + 1}. ${s.title}</span>`).join('<span class="arrow">→</span>')}
        </div>
        <div class="row spread">
          <span class="meta">${t.segments.length} инцидента подряд</span>
          <button class="primary" data-trip="${t.id}">В рейс</button>
        </div>
      </div>`
      )
      .join("")}

    <div class="card"><h3>Отдельные ситуации</h3>
      <div class="meta">Порядок подобран под ваш профиль: сверху непройденные и те, что дались хуже.</div>
    </div>
    ${scenarios
      .map(
        (s) => `
      <div class="card">
        <div class="row spread">
          <h3>${s.title}</h3>
          <span class="meta">${"★".repeat(s.difficulty)}</span>
        </div>
        <div class="meta">${s.segment} · вагон ${s.car_class} · до остановки ${s.minutes_to_stop} мин · ${s.nodes} узлов</div>
        <p>${s.summary}</p>
        <div class="row spread">
          <span class="meta">Источник: ${s.sources.join("; ")}</span>
          <button class="ghost" data-start="${s.id}">Пройти</button>
        </div>
      </div>`
      )
      .join("")}`;

  app.querySelectorAll("[data-start]").forEach((button) =>
    button.addEventListener("click", () => startRun({ scenario_id: button.dataset.start }))
  );
  app.querySelectorAll("[data-trip]").forEach((button) =>
    button.addEventListener("click", () => startRun({ trip_id: button.dataset.trip }))
  );
  app.querySelectorAll("[data-challenge]").forEach((button) =>
    button.addEventListener("click", () =>
      startRun({ scenario_id: button.dataset.challenge, challenge: true })
    )
  );
}

/* --- партия --- */

async function startRun(params) {
  state.run = await api("/runs", {
    method: "POST",
    body: JSON.stringify({ login: state.login, ...params }),
  });
  renderRun();
}

function stopTimer() {
  if (state.timer) {
    clearInterval(state.timer);
    state.timer = null;
  }
  if (state.typing) {
    clearInterval(state.typing);
    state.typing = null;
  }
}

function tripBar(trip) {
  if (!trip) return "";
  return `
    <div class="card trip-bar">
      <div class="row spread">
        <b>${trip.title}</b>
        <span class="meta">инцидент ${trip.position} из ${trip.total}</span>
      </div>
      <div class="steps">
        ${Array.from({ length: trip.total }, (_, i) =>
          `<i class="${i + 1 < trip.position ? "done" : i + 1 === trip.position ? "now" : ""}"></i>`
        ).join("")}
      </div>
      ${
        trip.memory.length
          ? `<div class="memory">Память рейса: ${trip.memory
              .map((m) => `<span class="chip">${m.label}</span>`)
              .join("")}</div>`
          : ""
      }
    </div>`;
}

function renderRun(lastEvent) {
  stopTimer();
  const run = state.run;
  if (run.finished) return renderDebrief();

  const node = run.node;
  const novel = state.novel && Boolean(node.scene);
  app.innerHTML =
    scales(run.loyalty, run.safety, lastEvent ? { loyalty: lastEvent.loyalty_delta, safety: lastEvent.safety_delta } : {}) +
    tripBar(run.trip) +
    `<div class="card ${novel ? "novel-card" : ""}">
      <div class="row spread">
        <span class="meta">${run.scenario.title} · ${run.scenario.segment}${
          run.scenario.minutes_to_stop ? ` · до остановки ${run.scenario.minutes_to_stop} мин` : ""
        }</span>
        <span class="row">
          ${node.critical ? '<span class="critical-tag">критическое решение</span>' : ""}
          ${node.scene ? `<button class="mode" id="mode">${state.novel ? "Текстом" : "Новеллой"}</button>` : ""}
        </span>
      </div>
      ${node.timer ? `
        <div class="timer-wrap">
          <div class="timer-text"><span>Время на решение</span><b id="tleft">${node.timer} с</b></div>
          <div class="timer-bar" id="tbar"><i style="width:100%"></i></div>
        </div>` : ""}
      ${novel ? stageBlock(node) : `
        <div class="speech">
          <div class="speaker">${speakerName(node.speaker)}</div>
          <div>${node.text}</div>
        </div>`}
      <div class="options">
        ${node.options
          .map(
            (o) => `<button class="option" data-option="${o.id}">${o.text}
              ${o.step ? `<span class="step">Шаг ролевой модели: ${state.reference.steps[o.step] || o.step}</span>` : ""}
            </button>`
          )
          .join("")}
      </div>
    </div>` +
    (lastEvent ? eventCard(lastEvent) : "");

  app.querySelectorAll("[data-option]").forEach((button) =>
    button.addEventListener("click", () => choose(button.dataset.option))
  );
  const mode = document.getElementById("mode");
  if (mode) {
    mode.addEventListener("click", () => {
      state.novel = !state.novel;
      localStorage.setItem("vsm_novel", state.novel ? "on" : "off");
      renderRun(lastEvent);
    });
  }
  if (novel) startScene(node);
  if (node.timer) runTimer(node.timer);
}

/* Сцена новеллы: фон, персонаж, реплика. Картинок может не быть —
   тогда остаётся градиент по имени сцены и табличка с именем. */
function stageBlock(node) {
  const who = node.character;
  return `
    <div class="stage" data-scene="${node.scene}">
      ${node.scene_image ? `<img class="bg" src="${node.scene_image}" alt="" onerror="this.remove()">` : ""}
      ${
        who
          ? `<div class="actor mood-${who.mood}">
               <img src="${who.sprite}" alt="" onerror="this.remove()">
             </div>`
          : ""
      }
      <div class="dialogue">
        <div class="who">${who ? `${who.name}<span class="role"> · ${who.role}</span>` : speakerName(node.speaker)}</div>
        <div class="line" id="line"></div>
      </div>
    </div>`;
}

function startScene(node) {
  const line = document.getElementById("line");
  if (!line) return;
  const text = node.text;
  let shown = 0;
  const reveal = () => {
    shown = text.length;
    line.textContent = text;
    clearInterval(state.typing);
    state.typing = null;
  };
  line.textContent = "";
  clearInterval(state.typing);
  state.typing = setInterval(() => {
    shown += 2;
    line.textContent = text.slice(0, shown);
    if (shown >= text.length) reveal();
  }, 16);
  line.parentElement.addEventListener("click", reveal);   // клик — показать реплику целиком
}

function speakerName(speaker) {
  return { passenger: "Пассажир", chief: "Начальник поезда", radio: "Рация", narrator: "Вагон" }[speaker] || speaker;
}

function runTimer(seconds) {
  const started = Date.now();
  const left = document.getElementById("tleft");
  const bar = document.getElementById("tbar");
  state.timer = setInterval(() => {
    const passed = (Date.now() - started) / 1000;
    const remain = Math.max(0, seconds - passed);
    left.textContent = `${remain.toFixed(0)} с`;
    bar.firstElementChild.style.width = `${(remain / seconds) * 100}%`;
    bar.classList.toggle("hot", remain < seconds * 0.35);
    if (remain <= 0) {
      stopTimer();
      choose(null);            // сервер подтвердит истечение по своим часам
    }
  }, 100);
}

async function choose(optionId) {
  stopTimer();
  app.querySelectorAll("[data-option]").forEach((b) => (b.disabled = true));
  const result = await api(`/runs/${state.run.run_id}/choose`, {
    method: "POST",
    body: JSON.stringify({ option_id: optionId }),
  });
  const event = result.event;
  state.run = result;
  if (result.finished) {
    renderDebrief();
  } else if (result.segment_done) {
    renderSegmentDone(result.segment_done, event);
  } else {
    renderRun(event);
  }
}

/* Перегон пройден, но рейс продолжается: пауза между инцидентами. */
function renderSegmentDone(segment, event) {
  stopTimer();
  const run = state.run;
  const verdict = { good: "Инцидент закрыт", neutral: "Инцидент закрыт с осадком", bad: "Инцидент закрыт плохо" };
  app.innerHTML =
    scales(run.loyalty, run.safety) +
    tripBar(run.trip) +
    `<div class="card">
      <h3>${verdict[segment.ending] || "Инцидент закрыт"}: ${segment.title}</h3>
      <div class="speech"><div>${segment.text}</div></div>
      <p class="meta">Шкалы и то, что пассажиры запомнили, переходят в следующий инцидент рейса.</p>
      <button class="primary" id="next-segment">Дальше по маршруту</button>
    </div>` +
    eventCard(event);
  document.getElementById("next-segment").addEventListener("click", () => renderRun());
}

function eventCard(event) {
  return `
    <div class="card">
      <div class="meta">Ваш ход: ${event.option_text}</div>
      <div class="event">
        <div class="reasons">${event.reasons.map((r) => `• ${r}`).join("<br>")}</div>
        ${event.better ? `<div class="better">Как лучше: ${event.better}</div>` : ""}
        ${alternativeBlock(event)}
      </div>
    </div>`;
}

function alternativeBlock(event) {
  if (!event.alternative) return "";
  const a = event.alternative;
  return `<div class="alt">Что было бы, если: «${escapeHtml(a.text)}» —
    ${a.reason} <span class="meta">(лояльность ${a.loyalty >= 0 ? "+" : ""}${a.loyalty},
    безопасность ${a.safety >= 0 ? "+" : ""}${a.safety})</span></div>`;
}

/* --- разбор --- */

async function renderDebrief() {
  stopTimer();
  const data = await api(`/runs/${state.run.run_id}/debrief`);
  const result = data.result;
  const titles = data.competence_titles;
  const endings = { good: "✅", neutral: "➖", bad: "❌" };

  app.innerHTML = `
    <div class="card">
      <div class="row spread">
        <h3>Разбор: ${data.trip ? data.trip.title : data.scenario.title}</h3>
        <span class="meta">${result.grade} · ${result.score} баллов · +${result.xp} опыта</span>
      </div>
      ${scales(result.loyalty, result.safety)}
      <div class="meta">Пропущено таймеров: ${result.timeouts}${
        result.streak ? ` · серия ${result.streak} дн.` : ""
      }</div>
      ${
        result.segments.length > 1
          ? `<div class="chain">${result.segments
              .map((s) => `<span class="link">${endings[s.ending] || ""} ${s.scenario_id}</span>`)
              .join('<span class="arrow">→</span>')}</div>`
          : ""
      }
      ${result.earned_achievements && result.earned_achievements.length
        ? `<p>Новые достижения: ${result.earned_achievements.map((a) => `${a.icon} ${a.title}`).join(", ")}</p>`
        : ""}
    </div>
    <div class="card">
      <h3>Что это значит</h3>
      ${data.advice.map((a) => `<p>${a}</p>`).join("")}
    </div>
    <div class="card">
      <h3>Компетенции за рейс</h3>
      <div class="comp">
        ${Object.entries(result.competences)
          .map(
            ([key, value]) => `
            <div class="line"><span>${titles[key]}</span><b>${value > 0 ? "+" : ""}${value}</b></div>
            <div class="track ${value < 0 ? "neg" : ""}"><i style="width:${Math.min(100, Math.abs(value) * 12)}%"></i></div>`
          )
          .join("")}
      </div>
    </div>
    ${data.parts
      .map(
        (part) => `
      <div class="card">
        <h3>${part.title}</h3>
        <div class="meta">${part.segment}</div>
        ${part.events.map(eventRow).join("")}
        <div class="meta">Нормативная основа: ${part.sources.join("; ")}</div>
      </div>`
      )
      .join("")}
    <div class="row">
      <button class="primary" id="again">Ещё рейс</button>
      <button class="ghost" id="to-profile">В профиль</button>
    </div>`;

  document.getElementById("again").addEventListener("click", () => switchTo("catalog"));
  document.getElementById("to-profile").addEventListener("click", () => switchTo("profile"));
}

function eventRow(e) {
  return `
    <div class="event">
      <div class="meta">${e.timed_out ? "⏱ время вышло" : `${e.seconds} с${e.timer ? ` из ${e.timer}` : ""}`} ·
        лояльность ${e.loyalty_delta >= 0 ? "+" : ""}${e.loyalty_delta} ·
        безопасность ${e.safety_delta >= 0 ? "+" : ""}${e.safety_delta}</div>
      <div><b>${e.option_text}</b></div>
      <div class="reasons">${e.reasons.map((r) => `• ${r}`).join("<br>")}</div>
      ${e.better ? `<div class="better">Как лучше: ${e.better}</div>` : ""}
      ${alternativeBlock(e)}
    </div>`;
}

/* --- профиль, рейтинг, аналитика, уведомления --- */

async function viewProfile() {
  const [profile, streak] = await Promise.all([
    api(`/conductors/${encodeURIComponent(state.login)}`),
    api(`/conductors/${encodeURIComponent(state.login)}/streak`),
  ]);
  const titles = profile.competence_titles;
  app.innerHTML = `
    <div class="card">
      <div class="row spread">
        <h3>${profile.display_name}</h3>
        <span class="meta">${profile.level.name}</span>
      </div>
      <div class="meta">${profile.brigade} · ${profile.depot}</div>
      <div class="timer-wrap">
        <div class="timer-text"><span>${profile.level.xp} опыта</span>
          <span>${profile.level.next_name ? `до «${profile.level.next_name}» — ${profile.level.xp_to_next}` : "высший уровень"}</span></div>
        <div class="timer-bar"><i style="width:${profile.level.next_name
          ? Math.min(100, (profile.level.xp / (profile.level.xp + profile.level.xp_to_next)) * 100)
          : 100}%"></i></div>
      </div>
      <div class="meta">Рейсов пройдено: ${profile.runs_completed} · средний балл: ${profile.average_score}
        · 🔥 серия ${streak.streak_days} дн.</div>
    </div>
    <div class="card">
      <h3>Компетенции</h3>
      <div class="comp">
        ${Object.entries(profile.competences)
          .map(
            ([key, value]) => `
            <div class="line"><span>${titles[key]}</span><b>${value > 0 ? "+" : ""}${value}</b></div>
            <div class="track ${value < 0 ? "neg" : ""}"><i style="width:${Math.min(100, Math.abs(value) * 6)}%"></i></div>`
          )
          .join("")}
      </div>
    </div>
    <div class="card">
      <h3>Достижения</h3>
      <div class="achv">
        ${profile.achievements
          .map((a) => `<div class="item ${a.earned ? "on" : ""}" title="${escapeHtml(a.description)}">${a.icon} ${a.title}</div>`)
          .join("")}
      </div>
    </div>
    <div class="card">
      <h3>История рейсов</h3>
      <table><tr><th>Сценарий</th><th>Балл</th><th>Оценка</th><th>Л / Б</th></tr>
      ${profile.history
        .map(
          (h) => `<tr><td>${h.scenario_id}</td><td>${h.score}</td><td>${h.grade}</td><td>${h.loyalty} / ${h.safety}</td></tr>`
        )
        .join("")}
      </table>
    </div>`;
}

async function viewLeaderboard() {
  const [rows, challenge] = await Promise.all([
    api("/leaderboard?scope=company"),
    api(`/challenge?login=${encodeURIComponent(state.login)}`),
  ]);
  app.innerHTML = `
    <div class="card challenge">
      <h3>🏁 Рейс недели · ${challenge.week}</h3>
      <div class="meta">${challenge.scenario.title} — один сценарий для всех бригад.</div>
      <table><tr><th>#</th><th>Проводник</th><th>Бригада</th><th>Лучший балл</th></tr>
      ${challenge.leaderboard
        .map((r) => `<tr><td>${r.place}</td><td>${r.display_name}</td><td>${r.brigade}</td><td>${r.best}</td></tr>`)
        .join("") || '<tr><td colspan="4" class="meta">Ещё никто не проходил</td></tr>'}
      </table>
    </div>
    <div class="card">
      <h3>Рейтинг проводников</h3>
      <div class="meta">Опыт начисляется за баллы рейса с поправкой на сложность сценария.</div>
      <table><tr><th>#</th><th>Проводник</th><th>Бригада</th><th>Уровень</th><th>Опыт</th><th>Средний балл</th></tr>
      ${rows
        .map(
          (r) => `<tr${r.login === state.login ? ' class="me"' : ""}>
            <td>${r.place}</td><td>${r.display_name}</td><td>${r.brigade}</td>
            <td>${r.level}</td><td>${r.xp}</td><td>${r.avg_score}</td></tr>`
        )
        .join("")}
      </table>
    </div>`;
}

async function viewAnalytics() {
  const [hotspots, trend] = await Promise.all([
    api("/analytics/hotspots?limit=8"),
    api(`/analytics/trend?login=${encodeURIComponent(state.login)}`),
  ]);
  app.innerHTML = `
    <div class="card">
      <h3>Ваша динамика</h3>
      <div class="meta">Сравнение первой и второй половины последних рейсов: что растёт, а что нет.</div>
      <div class="comp">
        ${trend.competences
          .map(
            (c) => `<div class="line"><span>${c.title}</span>
              <b class="${c.delta < 0 ? "down" : "up"}">${c.delta > 0 ? "+" : ""}${c.delta}</b></div>`
          )
          .join("")}
      </div>
      ${
        trend.points.length
          ? `<table><tr><th>Рейс</th><th>Сценарий</th><th>Балл</th></tr>
             ${trend.points
               .map((p, i) => `<tr><td>${i + 1}</td><td>${p.scenario_id}</td><td>${p.score}</td></tr>`)
               .join("")}</table>`
          : '<div class="meta">Пройдите пару рейсов — здесь появится динамика.</div>'
      }
    </div>
    <div class="card">
      <h3>Где ошибаются чаще всего</h3>
      <div class="meta">Развилки с наибольшей потерей шкал по всем прохождениям — данные
      для методистов о реальных пробелах в подготовке.</div>
      <table><tr><th>Сценарий</th><th>Узел</th><th>Прохождений</th><th>Средний ущерб</th><th>Таймаутов</th></tr>
      ${hotspots
        .map(
          (h) => `<tr><td>${h.scenario_id}</td><td>${h.node_id}</td><td>${h.attempts}</td>
            <td>${h.avg_damage}</td><td>${h.timeouts}</td></tr>`
        )
        .join("")}
      </table>
    </div>`;
}

async function viewNotifications() {
  const items = await api(`/notifications?login=${encodeURIComponent(state.login)}`);
  app.innerHTML =
    `<div class="card"><h3>Уведомления</h3><div class="meta">Новые сценарии, челленджи, назначения и сгорающие баллы.</div></div>` +
    items
      .map(
        (n) => `<div class="card" style="${n.read ? "opacity:.5" : ""}">
          <b>${n.title}</b><div class="meta">${n.body}</div>
        </div>`
      )
      .join("");
  items.filter((n) => !n.read).forEach((n) => api(`/notifications/${n.id}/read`, { method: "POST" }));
  updateBell(0);
}

function updateBell(count) {
  const bell = document.getElementById("bell");
  bell.textContent = count || "";
  bell.classList.toggle("on", Boolean(count));
}

/* --- навигация --- */

const VIEWS = {
  catalog: viewCatalog,
  profile: viewProfile,
  leaderboard: viewLeaderboard,
  analytics: viewAnalytics,
  notifications: viewNotifications,
};

function switchTo(view) {
  stopTimer();
  state.view = view;
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  VIEWS[view]().catch((error) => (app.innerHTML = `<div class="card">Ошибка: ${error.message}</div>`));
}

document.querySelectorAll("#tabs button").forEach((button) =>
  button.addEventListener("click", () => switchTo(button.dataset.view))
);

async function boot() {
  state.reference = await api("/reference");
  await api("/conductors", {
    method: "POST",
    body: JSON.stringify({
      login: state.login,
      display_name: "Смирнова А.",
      brigade: "Бригада 3",
      depot: "Депо Москва-Пассажирская",
    }),
  });
  localStorage.setItem("vsm_login", state.login);
  const profile = await api(`/conductors/${encodeURIComponent(state.login)}`);
  document.getElementById("who").innerHTML =
    `${profile.display_name} · ${profile.level.name}<br>${profile.brigade}, ${profile.depot}`;
  const notifications = await api(`/notifications?login=${encodeURIComponent(state.login)}`);
  updateBell(notifications.filter((n) => !n.read).length);
  switchTo("catalog");
}

boot();
