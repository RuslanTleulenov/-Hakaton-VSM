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

function el(html) {
  const wrap = document.createElement("div");
  wrap.innerHTML = html.trim();
  return wrap.firstElementChild;
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
  const scenarios = await api(`/scenarios?login=${encodeURIComponent(state.login)}`);
  app.innerHTML = `
    <div class="card">
      <h3>Смена началась</h3>
      <div class="meta">Рейсы подобраны под ваш профиль: сверху те, что вы ещё не проходили
      или прошли хуже всего.</div>
    </div>` +
    scenarios
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
          <button class="primary" data-start="${s.id}">В рейс</button>
        </div>
      </div>`
      )
      .join("");

  app.querySelectorAll("[data-start]").forEach((button) =>
    button.addEventListener("click", () => startRun(button.dataset.start))
  );
}

/* --- партия --- */

async function startRun(scenarioId) {
  state.run = await api("/runs", {
    method: "POST",
    body: JSON.stringify({ login: state.login, scenario_id: scenarioId }),
  });
  renderRun();
}

function stopTimer() {
  if (state.timer) {
    clearInterval(state.timer);
    state.timer = null;
  }
}

function renderRun(lastEvent) {
  stopTimer();
  const run = state.run;
  if (run.finished) return renderDebrief();

  const node = run.node;
  app.innerHTML =
    scales(run.loyalty, run.safety, lastEvent ? { loyalty: lastEvent.loyalty_delta, safety: lastEvent.safety_delta } : {}) +
    `<div class="card">
      <div class="row spread">
        <span class="meta">${run.scenario.title} · ${run.scenario.segment} · до остановки ${run.scenario.minutes_to_stop} мин</span>
        ${node.critical ? '<span class="critical-tag">критическое решение</span>' : ""}
      </div>
      ${node.timer ? `
        <div class="timer-wrap">
          <div class="timer-text"><span>Время на решение</span><b id="tleft">${node.timer} с</b></div>
          <div class="timer-bar" id="tbar"><i style="width:100%"></i></div>
        </div>` : ""}
      <div class="speech">
        <div class="speaker">${speakerName(node.speaker)}</div>
        <div>${node.text}</div>
      </div>
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

  if (node.timer) runTimer(node.timer);
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
    state.lastResult = result.result;
    renderDebrief();
  } else {
    renderRun(event);
  }
}

function eventCard(event) {
  return `
    <div class="card">
      <div class="meta">Ваш ход: ${event.option_text}</div>
      <div class="event">
        <div class="reasons">${event.reasons.map((r) => `• ${r}`).join("<br>")}</div>
        ${event.better ? `<div class="better">Как лучше: ${event.better}</div>` : ""}
      </div>
    </div>`;
}

/* --- разбор --- */

async function renderDebrief() {
  stopTimer();
  const data = await api(`/runs/${state.run.run_id}/debrief`);
  const result = data.result;
  const titles = data.competence_titles;

  app.innerHTML = `
    <div class="card">
      <div class="row spread">
        <h3>Разбор рейса: ${data.scenario.title}</h3>
        <span class="meta">${result.grade} · ${result.score} баллов · +${result.xp} опыта</span>
      </div>
      ${scales(result.loyalty, result.safety)}
      <div class="meta">Пропущено таймеров: ${result.timeouts}</div>
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
    <div class="card">
      <h3>Ход за ходом</h3>
      ${data.events
        .map(
          (e) => `
        <div class="event">
          <div class="meta">${e.timed_out ? "⏱ время вышло" : `${e.seconds} с${e.timer ? ` из ${e.timer}` : ""}`} ·
            лояльность ${e.loyalty_delta >= 0 ? "+" : ""}${e.loyalty_delta} ·
            безопасность ${e.safety_delta >= 0 ? "+" : ""}${e.safety_delta}</div>
          <div><b>${e.option_text}</b></div>
          <div class="reasons">${e.reasons.map((r) => `• ${r}`).join("<br>")}</div>
          ${e.better ? `<div class="better">Как лучше: ${e.better}</div>` : ""}
        </div>`
        )
        .join("")}
      <div class="meta">Нормативная основа: ${data.scenario.sources.join("; ")}</div>
    </div>
    <div class="row">
      <button class="primary" id="again">Ещё рейс</button>
      <button class="ghost" id="to-profile">В профиль</button>
    </div>`;

  document.getElementById("again").addEventListener("click", () => switchTo("catalog"));
  document.getElementById("to-profile").addEventListener("click", () => switchTo("profile"));
}

/* --- профиль, рейтинг, аналитика, уведомления --- */

async function viewProfile() {
  const profile = await api(`/conductors/${encodeURIComponent(state.login)}`);
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
      <div class="meta">Рейсов пройдено: ${profile.runs_completed} · средний балл: ${profile.average_score}</div>
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
          .map((a) => `<div class="item ${a.earned ? "on" : ""}" title="${a.description}">${a.icon} ${a.title}</div>`)
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
  const rows = await api("/leaderboard?scope=company");
  app.innerHTML = `
    <div class="card">
      <h3>Рейтинг проводников</h3>
      <div class="meta">Опыт начисляется за баллы рейса с поправкой на сложность сценария.</div>
      <table><tr><th>#</th><th>Проводник</th><th>Бригада</th><th>Уровень</th><th>Опыт</th><th>Средний балл</th></tr>
      ${rows
        .map(
          (r) => `<tr${r.login === state.login ? ' style="color:#fff"' : ""}>
            <td>${r.place}</td><td>${r.display_name}</td><td>${r.brigade}</td>
            <td>${r.level}</td><td>${r.xp}</td><td>${r.avg_score}</td></tr>`
        )
        .join("")}
      </table>
    </div>`;
}

async function viewAnalytics() {
  const hotspots = await api("/analytics/hotspots?limit=8");
  app.innerHTML = `
    <div class="card">
      <h3>Где ошибаются чаще всего</h3>
      <div class="meta">Развилки с наибольшей потерей шкал по всем прохождениям — это данные
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
    `<div class="card"><h3>Уведомления</h3><div class="meta">Новые сценарии, челленджи и сгорающие баллы.</div></div>` +
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
