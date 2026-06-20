/* ===== 热点商城 · 前端逻辑 =====
 * 全部数据走后端 API；像素 sprite 是 CSS box-shadow 拼出。
 */

const API = ""; // 同源

const SPRITES = {
  juicer: {
    palette: ["#ffffff", "#ff6b35", "#fbbf24", "#fef3c7", "#d97706"],
    grid: [
      "................",
      "................",
      "..AAAA..AAAA...",
      "..ACCA..ACCA...",
      "..ACCA..ACCA...",
      "..ABBA..ABBA...",
      "..A.AA..A.AA...",
      "..A.AA..A.AA...",
      "..AAAA..AAAA...",
      "..AAAA..AAAA...",
      "....B..B.......",
      "....B..B.......",
      "....B..B.......",
      "...BBBBBB......",
      "..BBBBBBBB.....",
      "...DDDD........",
    ],
  },
  earphone: {
    palette: ["#ffffff", "#1f2937", "#6b7280", "#2563eb", "#dbeafe"],
    grid: [
      "................",
      ".....CCCC......",
      "....CCCCC......",
      "....CC.CC......",
      "....CC.CC......",
      "....CC.CC......",
      "....CC.CC......",
      "...BBBBBBB.....",
      "..BBBBBBBBB....",
      ".BBBBBBBBBBB...",
      ".BBBBBBBBBBA...",
      ".BBBBBBBBBAA...",
      ".BBBBBBBBBAA...",
      "..BBBBBBBAA....",
      "...BBBBBAA.....",
      "................",
    ],
  },
  toothbrush: {
    palette: ["#ffffff", "#10b981", "#a7f3d0", "#374151", "#e5e7eb"],
    grid: [
      "................",
      "....BBBBBB.....",
      "...BBBBBBBB....",
      "...BBAAAAAB....",
      "....BAEEAB.....",
      "....BAEEAB.....",
      ".....BCCB......",
      ".....BCCB......",
      ".....BCCB......",
      ".....BCCB......",
      ".....BCCB......",
      ".....BCCB......",
      ".....BCCB......",
      ".....BCCB......",
      "....BCCCCB.....",
      "....BBBBBB.....",
    ],
  },
  sunscreen: {
    palette: ["#ffffff", "#f59e0b", "#fde68a", "#92400e", "#fff7ed"],
    grid: [
      "................",
      "..BBBBBBBBBB....",
      "..BAAAAAAAAAB...",
      "..BAAAAAAAAB....",
      "..BAAAAAAAAB....",
      "..BAAAAAAAAB....",
      "..BBBBBBBBBB....",
      ".....CCCC.......",
      "....CCCCC.......",
      "...CCCCC........",
      "....CCCC........",
      ".....CCC........",
      "......CC........",
      ".......C........",
      "................",
      "................",
    ],
  },
  airfryer: {
    palette: ["#ffffff", "#1f2937", "#9ca3af", "#fbbf24", "#fef3c7"],
    grid: [
      "................",
      "...BBBBBBBBBB...",
      "..BAAAAAAAAAAB..",
      "..BABBBBBBABAB..",
      "..BABCDDDDCBAB..",
      "..BABCDDDDCBAB..",
      "..BABCDDDDCBAB..",
      "..BABBBBBBABAB..",
      "..BAAAAAAAAAAB..",
      "..BABBEEBBBAB...",
      "..BABBEEDBBB....",
      "..BABBEEBBB.....",
      "..BAAAAAAB......",
      "..BBBBBBB.......",
      "...BBBBB........",
      "................",
    ],
  },
  tent: {
    palette: ["#ffffff", "#dc2626", "#fbbf24", "#1f2937", "#fef2f2"],
    grid: [
      "................",
      "................",
      ".......B........",
      "......BBB.......",
      ".....BABAB......",
      "....BAABBAB.....",
      "...BAAAAAAB.....",
      "..BAAAAAAAAB....",
      ".BAAAAAAAAAAB...",
      "BAAAAAAAAAAAAB..",
      "BAAAAAAAAAAAAB..",
      "BBDDDDDDDDDDBB..",
      "BDD.........DDB.",
      "BBDDDDDDDDDDBB..",
      "................",
      "................",
    ],
  },
  yogamat: {
    palette: ["#ffffff", "#8b5cf6", "#c4b5fd", "#1f2937", "#ede9fe"],
    grid: [
      "................",
      "................",
      "....BB......BB..",
      "...BBBB....BBBB.",
      "..BBBBBB..BBBBBB",
      ".BBBBBBBBBBBBBBB",
      "BBBBBBBBBBBBBBBB",
      ".BBBBBBBBBBBBBBB",
      "..BBBBBBBBBBBBBB",
      "...BBBBBBBBBBBB.",
      "....BBBBBBBBBB..",
      ".....BBBBBBBB...",
      "......BBBBBB....",
      ".......BBBB.....",
      "........BB......",
      "................",
    ],
  },
  tshirt: {
    palette: ["#ffffff", "#3b82f6", "#93c5fd", "#1f2937", "#dbeafe"],
    grid: [
      "................",
      "....BB....BB....",
      "...BBBB..BBBB...",
      "..BBBBBBBBBBBB..",
      ".BBBBBBBBBBBBBB.",
      "BBBBBBBBBBBBBBBB",
      "BBBBAABBBBBAABBB",
      "BBBAAAAAAEAAABBB",
      "BBBAAAAAAAAAABBB",
      "BBBAAAAAAAAAABBB",
      "BBBAAAAAAAAAABBB",
      "BBBAAAAAAAAAABBB",
      ".BBBAAAAAAAAABBB",
      "..BBBAAAAAAAABB.",
      "...BBBAAAAABBB..",
      "....BBBAABBB....",
    ],
  },
  laptop: {
    palette: ["#ffffff", "#374151", "#9ca3af", "#2563eb", "#e5e7eb"],
    grid: [
      "................",
      "................",
      "..BBBBBBBBBBBB..",
      "..BAAAAAAAAAAB..",
      "..BACCCCCCCAB...",
      "..BACCDDDDCCAB..",
      "..BACCDDDDCCAB..",
      "..BACCDDDDCCAB..",
      "..BACCDDDDCCAB..",
      "..BACCCCCCCAB...",
      "..BAAAAAAAAAAB..",
      "..BBBBBBBBBBBB..",
      "..BBBBBBBBBBBB..",
      ".EEEEEEEEEEEEEE.",
      "EAAAAAAAAAAAAAA.",
      "................",
    ],
  },
  camera: {
    palette: ["#ffffff", "#1f2937", "#4b5563", "#fbbf24", "#d1d5db"],
    grid: [
      "................",
      "..........DD....",
      "..BBBBBBBBBB....",
      ".BCCCCCCCCCB....",
      ".BCAAABAAACB....",
      ".BCABBBBABCB....",
      ".BCABBBBABCB....",
      ".BCAAABAAACB....",
      ".BCCCCCCCCCB....",
      "..BBBBBBBBBB....",
      "....EEEE........",
      "................",
      "................",
      "................",
      "................",
      "................",
    ],
  },
  shoes: {
    palette: ["#ffffff", "#dc2626", "#fecaca", "#1f2937", "#fee2e2"],
    grid: [
      "................",
      "................",
      "................",
      "................",
      ".....BB.........",
      "....BBBB........",
      "...BBBBBB.......",
      "..BBBBBBB.......",
      ".BBBBBBBB.......",
      "BBBBBBBBB.......",
      "BBABBBBBBBB.....",
      "BBBBBBBBBBBB....",
      "..CC..CC........",
      "................",
      "................",
      "................",
    ],
  },
  watch: {
    palette: ["#ffffff", "#1f2937", "#6b7280", "#10b981", "#d1d5db"],
    grid: [
      "................",
      "................",
      "......BB........",
      ".....BCCB.......",
      "....BCCCCB......",
      "..BBCCCCBB......",
      ".BCCDDAADCCB....",
      "BCCDDAEADDCCB...",
      "BCCDDDAADDCCB...",
      "BCCDDDDDDDCCB...",
      "BCCDDDAADDCCB...",
      ".BCCDDDDDDCCB...",
      "..BCCDDDDDCB....",
      "....BCCCCB......",
      ".....BCCB.......",
      "......BB........",
    ],
  },
};

const PALETTE_LETTERS = {
  ".": null,
  A: 1, B: 2, C: 3, D: 4, E: 5,
};

function spriteToBoxShadow(sprite) {
  const def = SPRITES[sprite];
  if (!def) return "";
  const shadows = [];
  for (let y = 0; y < 16; y++) {
    const row = def.grid[y] || "";
    for (let x = 0; x < 16; x++) {
      const ch = row[x] || ".";
      const colorIdx = PALETTE_LETTERS[ch];
      if (colorIdx == null) continue;
      const color = def.palette[colorIdx];
      shadows.push(`${x * 2}px ${y * 2}px 0 ${color}`);
    }
  }
  return shadows.join(",");
}

function applySprite(el, sprite) {
  if (!el) return;
  el.style.boxShadow = spriteToBoxShadow(sprite);
}

/* ===== 后端拉取 ===== */

async function apiGet(path) {
  const r = await fetch(API + path, { headers: { Accept: "application/json" } });
  if (!r.ok) throw new Error(`GET ${path} -> ${r.status}`);
  return r.json();
}

async function apiPost(path) {
  const r = await fetch(API + path, { method: "POST", headers: { Accept: "application/json" } });
  if (!r.ok) throw new Error(`POST ${path} -> ${r.status}`);
  return r.json();
}

/* ===== 工具 ===== */

function fmtTime(iso) {
  if (!iso) return "--:--:--";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "--:--:--";
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function fmtAgo(iso) {
  if (!iso) return "尚未运行";
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 0) return "刚刚";
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s} 秒前`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m} 分钟前`;
  const h = Math.floor(m / 60);
  return `${h} 小时前`;
}

function escHtml(s) {
  if (s == null) return "";
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/* ===== 渲染 ===== */

function renderScenes(scenes) {
  const bar = document.getElementById("scenes-bar");
  if (!bar) return;
  if (!scenes || !scenes.length) {
    bar.innerHTML = '<span style="font-size:12px;color:var(--text-muted);">暂无场景</span>';
    return;
  }
  bar.innerHTML = scenes
    .map(
      (s) =>
        `<button class="scene-chip" data-scene-id="${escHtml(s.id)}" type="button">` +
        `<span>#${escHtml(s.title)}</span>` +
        `<span class="scene-chip__conf">${(s.confidence * 100).toFixed(0)}%</span>` +
        `</button>`
    )
    .join("");
}

function renderProducts(items, options = {}) {
  const grid = document.getElementById("product-grid");
  if (!grid) return;
  if (!items || !items.length) {
    grid.innerHTML = '<div class="empty">没有匹配的商品</div>';
    return;
  }
  grid.innerHTML = items
    .map((rec) => {
      const p = rec.product || rec;
      const scene = rec.scene;
      const tags = (p.tags || []).slice(0, 3);
      const reason = rec.reason || "";
      return `
        <article class="product-card" data-product-id="${escHtml(p.id)}">
          <div class="product-card__sprite" data-sprite="${escHtml(p.sprite)}" style="width:32px;height:32px;"></div>
          <h3 class="product-card__title">${escHtml(p.title)}</h3>
          <div class="product-card__price-row">
            <span class="product-card__price"><span class="product-card__price-symbol">¥</span>${p.price}</span>
            ${p.origPrice && p.origPrice > p.price
              ? `<span class="product-card__orig-price">¥${p.origPrice}</span>`
              : ""}
          </div>
          ${tags.length
            ? `<div class="product-card__tags">${tags.map((t) => `<span class="product-card__tag">${escHtml(t)}</span>`).join("")}</div>`
            : ""}
          ${scene
            ? `<div class="product-card__scene">${escHtml(scene.title)}</div>`
            : ""}
          ${reason
            ? `<div class="product-card__reason">${escHtml(reason)}</div>`
            : ""}
        </article>`;
    })
    .join("");

  // 应用像素 sprite（box-shadow 到 32x32 容器）
  grid.querySelectorAll(".product-card__sprite").forEach((el) => {
    const sprite = el.getAttribute("data-sprite");
    applySprite(el, sprite);
  });
}

const AGENT_META = {
  sense:   { name: "感知 Agent",   avatar: "🛰️", task: "抓取热点 / 提取消费场景" },
  match:   { name: "挂品 Agent",   avatar: "🛒", task: "场景-商品匹配 / 入关联库" },
  copy:    { name: "导购生成 Agent", avatar: "✍️", task: "生成推荐理由 / 标签" },
  deliver: { name: "分发 Agent",   avatar: "📡", task: "响应首页 / 搜索请求" },
};

function renderAgents(statusData, logsData) {
  const wrap = document.getElementById("agents");
  if (!wrap) return;

  const order = ["sense", "match", "copy", "deliver"];
  const statusByType = Object.fromEntries((statusData.agents || []).map((a) => [a.type, a]));
  const logsByType = Object.fromEntries((logsData.agents || []).map((a) => [a.type, a.logs || []]));

  wrap.innerHTML = order
    .map((type) => {
      const meta = AGENT_META[type];
      const s = statusByType[type] || { status: "idle", current_task: meta.task };
      const logs = logsByType[type] || [];
      const isRunning = s.status === "running";
      return `
        <div class="agent-card ${isRunning ? "is-running" : ""}">
          <div class="agent-card__head">
            <div class="agent-card__avatar">${meta.avatar}</div>
            <div class="agent-card__name">${meta.name}</div>
            <div class="agent-card__status">
              <span class="agent-card__status-dot ${isRunning ? "is-running" : ""}"></span>
              <span>${isRunning ? "运行中" : s.status === "error" ? "错误" : "就绪"}</span>
            </div>
          </div>
          <div class="agent-card__task">${escHtml(s.current_task || meta.task)}</div>
          ${
            logs.length
              ? `<ul class="agent-card__logs">${logs
                  .slice(-6)
                  .map(
                    (l) => `
                <li class="agent-card__log">
                  <span class="agent-card__log-time">${fmtTime(l.created_at)}</span>
                  <span class="agent-card__log-level is-${escHtml(l.level || "info")}">${escHtml((l.level || "info").toUpperCase())}</span>
                  <span class="agent-card__log-msg">${escHtml(l.message)}</span>
                </li>`
                  )
                  .join("")}</ul>`
              : `<div class="agent-card__empty">暂无日志</div>`
          }
        </div>`;
    })
    .join("");
}

function renderPipelineStatus(pipelineData) {
  const pill = document.getElementById("pipeline-status-pill");
  const dot = document.getElementById("pipeline-status-dot");
  const text = document.getElementById("pipeline-status-text");
  const meta = document.getElementById("pipeline-meta");
  const btn = document.getElementById("run-pipeline-btn");

  if (!pill) return;

  if (pipelineData.running) {
    pill.classList.add("is-running");
    pill.classList.remove("is-error");
    text.textContent = "流水线运行中";
    if (btn) btn.disabled = true;
  } else if (pipelineData.last_status === "error") {
    pill.classList.add("is-error");
    pill.classList.remove("is-running");
    text.textContent = "上次出错";
    if (btn) btn.disabled = false;
  } else {
    pill.classList.remove("is-running", "is-error");
    text.textContent = "系统就绪";
    if (btn) btn.disabled = false;
  }

  if (meta) {
    const last = fmtAgo(pipelineData.last_run_at);
    const next = pipelineData.next_run_in != null
      ? ` / 下次 ${Math.max(0, Math.round(pipelineData.next_run_in / 60))} 分钟后`
      : "";
    meta.textContent = `流水线状态：上次运行 ${last}${next}`;
  }
}

function renderContentHeader(title, count) {
  const t = document.getElementById("content-title");
  const m = document.getElementById("content-meta");
  if (t) t.textContent = title;
  if (m) m.textContent = `共 ${count} 个推荐`;
}

/* ===== 数据流 ===== */

let currentMode = "home"; // home | search
let currentQuery = "";
let pollTimer = null;

async function loadHome() {
  currentMode = "home";
  currentQuery = "";
  const [recs, scenes, statusData, logsData] = await Promise.all([
    apiGet("/api/recommend?limit=12"),
    apiGet("/api/scenes"),
    apiGet("/api/agents/status"),
    apiGet("/api/agents/logs?limit_per_agent=6"),
  ]);
  renderScenes(scenes.scenes || []);
  renderProducts(recs || []);
  renderContentHeader("热门推荐", (recs || []).length);
  renderAgents(statusData, logsData);
  renderPipelineStatus(statusData.pipeline || {});
}

async function loadSearch(q) {
  currentMode = "search";
  currentQuery = q;
  const url = `/api/search?q=${encodeURIComponent(q)}`;
  const [data, statusData, logsData] = await Promise.all([
    apiGet(url),
    apiGet("/api/agents/status"),
    apiGet("/api/agents/logs?limit_per_agent=6"),
  ]);
  renderProducts(data.items || []);
  renderContentHeader(`搜索：${q}`, (data.items || []).length);
  renderAgents(statusData, logsData);
  renderPipelineStatus(statusData.pipeline || {});
}

async function pollAgents() {
  try {
    const [statusData, logsData] = await Promise.all([
      apiGet("/api/agents/status"),
      apiGet("/api/agents/logs?limit_per_agent=6"),
    ]);
    renderAgents(statusData, logsData);
    renderPipelineStatus(statusData.pipeline || {});
  } catch (e) {
    console.warn("pollAgents error:", e);
  }
}

async function refreshContent() {
  try {
    if (currentMode === "search" && currentQuery) {
      await loadSearch(currentQuery);
    } else {
      await loadHome();
    }
  } catch (e) {
    console.error("refreshContent error:", e);
  }
}

/* ===== 事件绑定 ===== */

function bindEvents() {
  const input = document.getElementById("search-input");
  const btn = document.getElementById("search-btn");
  const runBtn = document.getElementById("run-pipeline-btn");
  const scenesBar = document.getElementById("scenes-bar");

  const doSearch = () => {
    const q = (input.value || "").trim();
    if (q) loadSearch(q);
    else loadHome();
  };

  if (btn) btn.addEventListener("click", doSearch);
  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") doSearch();
    });
  }

  if (scenesBar) {
    scenesBar.addEventListener("click", (e) => {
      const chip = e.target.closest(".scene-chip");
      if (!chip) return;
      const id = chip.getAttribute("data-scene-id");
      // 切到搜索模式，把场景标题作为关键词
      if (input) input.value = chip.querySelector("span")?.textContent?.replace(/^#/, "") || "";
      // 高亮
      scenesBar.querySelectorAll(".scene-chip").forEach((c) => c.classList.remove("is-active"));
      chip.classList.add("is-active");
      doSearch();
    });
  }

  if (runBtn) {
    runBtn.addEventListener("click", async () => {
      runBtn.disabled = true;
      runBtn.textContent = "运行中…";
      try {
        await apiPost("/api/run");
      } catch (e) {
        console.error("run pipeline error:", e);
      } finally {
        // 立即拉一次最新状态
        setTimeout(async () => {
          await pollAgents();
          runBtn.disabled = false;
          runBtn.textContent = "立即跑流水线";
        }, 500);
      }
    });
  }
}

/* ===== 启动 ===== */

async function init() {
  bindEvents();
  await loadHome();
  // 启动后每 3 秒轮询 Agent 状态 / 日志
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(pollAgents, 3000);
  // 流水线跑完后（约 10 秒）刷新一次商品列表
  setTimeout(refreshContent, 11000);
}

document.addEventListener("DOMContentLoaded", init);
