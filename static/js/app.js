/* Crypto Airdrop Tracker — フロントエンドロジック */

let activeFilters = { status: "all", difficulty: "all", hotOnly: false, search: "" };
let sortState = { col: null, dir: 1 };

function applyFilters() {
  const rows = document.querySelectorAll("#airdrop-tbody .airdrop-row");
  const hotCards = document.querySelectorAll(".hot-card");
  let visible = 0;

  rows.forEach(row => {
    const status     = row.dataset.status;
    const difficulty = row.dataset.difficulty;
    const hot        = row.dataset.hot === "true";
    const name       = row.dataset.name || "";

    const statusOk = activeFilters.status === "all" || status === activeFilters.status;
    const diffOk   = activeFilters.difficulty === "all" || difficulty === activeFilters.difficulty;
    const hotOk    = !activeFilters.hotOnly || hot;
    const searchOk = !activeFilters.search || name.includes(activeFilters.search.toLowerCase());

    const show = statusOk && diffOk && hotOk && searchOk;
    row.classList.toggle("hidden", !show);
    if (show) visible++;
  });

  hotCards.forEach(card => {
    const status     = card.dataset.status;
    const difficulty = card.dataset.difficulty;
    const name       = card.dataset.name || "";
    const statusOk = activeFilters.status === "all" || status === activeFilters.status;
    const diffOk   = activeFilters.difficulty === "all" || difficulty === activeFilters.difficulty;
    const searchOk = !activeFilters.search || name.includes(activeFilters.search.toLowerCase());
    card.style.display = (statusOk && diffOk && searchOk) ? "" : "none";
  });

  const badge = document.getElementById("visible-count");
  if (badge) badge.textContent = visible;
}

function filterAirdrops(type, value, btn) {
  activeFilters[type] = value;
  const group = btn.closest(".filter-buttons");
  if (group) {
    group.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  }
  applyFilters();
}

function filterHotOnly(btn) {
  activeFilters.hotOnly = !activeFilters.hotOnly;
  btn.classList.toggle("active", activeFilters.hotOnly);
  applyFilters();
}

function searchAirdrops(value) {
  activeFilters.search = value.trim().toLowerCase();
  applyFilters();
}

function sortTable(col) {
  if (sortState.col === col) {
    sortState.dir *= -1;
  } else {
    sortState.col = col;
    sortState.dir = 1;
  }

  const tbody = document.getElementById("airdrop-tbody");
  const rows  = Array.from(tbody.querySelectorAll(".airdrop-row"));

  rows.sort((a, b) => {
    if (col === "estimated_value_usd" || col === "value") {
      const av = parseFloat(a.dataset.value || "0");
      const bv = parseFloat(b.dataset.value || "0");
      return (av - bv) * sortState.dir;
    }
    const av = a.dataset[col] || a.querySelector(`td:nth-child(${colIndex(col)})`).textContent.trim();
    const bv = b.dataset[col] || b.querySelector(`td:nth-child(${colIndex(col)})`).textContent.trim();
    return av.localeCompare(bv, "ja") * sortState.dir;
  });

  rows.forEach(row => tbody.appendChild(row));
}

function colIndex(col) {
  const map = { name: 1, category: 2, type: 3, estimated_value_usd: 4, difficulty: 5, status: 6, end_date: 7 };
  return map[col] || 1;
}

/* ===== カウントダウン表示 ===== */
function renderCountdowns() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  document.querySelectorAll("[data-enddate]").forEach(el => {
    const raw = el.dataset.enddate;
    if (!raw || raw === "未定" || raw === "TBD") return;

    const end = new Date(raw);
    if (isNaN(end.getTime())) return;

    end.setHours(0, 0, 0, 0);
    const diffDays = Math.round((end - today) / 86400000);

    const existing = el.querySelector(".countdown-chip");
    if (existing) existing.remove();

    if (diffDays < 0) return;

    const chip = document.createElement("span");
    chip.className = "countdown-chip" + (diffDays <= 7 ? " urgent" : "");
    chip.textContent = diffDays === 0 ? "本日まで" : `残${diffDays}日`;
    el.appendChild(chip);
  });
}

/* ===== 次回更新までのカウントダウン ===== */
function updateNextUpdateCountdown() {
  const el = document.getElementById("next-update-countdown");
  if (!el) return;

  const now = new Date();
  const nextUpdate = new Date();
  nextUpdate.setHours(8, 0, 0, 0);
  if (now >= nextUpdate) nextUpdate.setDate(nextUpdate.getDate() + 1);

  const diff = nextUpdate - now;
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  el.textContent = `毎日 08:00 JST (あと ${h}時間${m}分)`;
}

/* ===== 自動更新チェック (10分ごと) ===== */
let _lastKnownTimestamp = null;

function scheduleAutoRefresh() {
  setTimeout(async () => {
    try {
      const res = await fetch("/api/updates");
      const updates = await res.json();
      if (updates.length > 0) {
        const latest = updates[0].timestamp;
        if (_lastKnownTimestamp === null) {
          _lastKnownTimestamp = latest;
        } else if (latest !== _lastKnownTimestamp) {
          showRefreshNotice(updates[0]);
          _lastKnownTimestamp = latest;
        }
      }
    } catch (_) {}
    scheduleAutoRefresh();
  }, 10 * 60 * 1000);
}

function showRefreshNotice(update) {
  const existing = document.getElementById("refresh-notice");
  if (existing) existing.remove();

  const notice = document.createElement("div");
  notice.id = "refresh-notice";

  let detail = "";
  if (update && update.added_count > 0) {
    detail = ` 🆕 新着 ${update.added_count}件`;
    if (update.hot_count > 0) detail += ` 🔥 ホット${update.hot_count}件`;
  }

  notice.style.cssText = [
    "position:fixed", "bottom:24px", "right:24px",
    "background:linear-gradient(135deg,#7c4dff,#651fff)",
    "color:white", "padding:16px 22px", "border-radius:12px",
    "font-size:14px", "font-weight:700", "cursor:pointer",
    "z-index:9999", "box-shadow:0 4px 24px rgba(124,77,255,0.6)",
    "max-width:320px", "line-height:1.5",
  ].join(";");
  notice.innerHTML = `🔄 新しい更新があります${detail}<br><span style="font-size:12px;opacity:0.85">クリックで再読み込み</span>`;
  notice.onclick = () => location.reload();
  document.body.appendChild(notice);

  setTimeout(() => notice.remove(), 20000);
}

/* ===== 初期化 ===== */
document.addEventListener("DOMContentLoaded", () => {
  renderCountdowns();
  updateNextUpdateCountdown();
  setInterval(updateNextUpdateCountdown, 60000);

  scheduleAutoRefresh();

  // テーブル行ツールチップ
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });
});
