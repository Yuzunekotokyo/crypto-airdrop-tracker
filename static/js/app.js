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
  const rows = Array.from(tbody.querySelectorAll(".airdrop-row"));

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

/* ===== 変更詳細の折りたたみ ===== */
function toggleChanges() {
  const body  = document.getElementById("update-changes");
  const arrow = document.getElementById("changes-arrow");
  if (!body) return;
  const open = body.style.display === "none" || body.style.display === "";
  body.style.display  = open ? "block" : "none";
  if (arrow) arrow.textContent = open ? "▲" : "▼";
}

/* ===== 次回更新カウントダウン ===== */
function startCountdown() {
  const el = document.getElementById("countdown-timer");
  if (!el) return;

  const target = new Date(el.dataset.target);
  if (isNaN(target.getTime())) return;

  function tick() {
    const now  = new Date();
    const diff = target - now;

    if (diff <= 0) {
      el.textContent = "更新中...";
      setTimeout(() => location.reload(), 5000);
      return;
    }

    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);

    el.textContent = `${h}時間 ${String(m).padStart(2,"0")}分 ${String(s).padStart(2,"0")}秒`;
    setTimeout(tick, 1000);
  }

  tick();
}

/* ===== 自動リロード: 30分ごとに新規更新確認 ===== */
let _lastKnownTimestamp = null;

function scheduleAutoRefresh() {
  setTimeout(() => {
    fetch("/api/updates")
      .then(r => r.json())
      .then(updates => {
        if (!updates.length) return;
        const latest = updates[0].timestamp;
        if (_lastKnownTimestamp === null) {
          _lastKnownTimestamp = latest;
        } else if (latest !== _lastKnownTimestamp) {
          showRefreshToast();
        }
      })
      .catch(() => {})
      .finally(() => scheduleAutoRefresh());
  }, 30 * 60 * 1000);
}

function showRefreshToast() {
  if (document.querySelector(".refresh-toast")) return;

  const toast = document.createElement("div");
  toast.className = "refresh-toast";
  toast.textContent = "🔄 新しい更新があります — クリックで再読み込み";
  toast.onclick = () => location.reload();
  document.body.appendChild(toast);

  setTimeout(() => {
    if (toast.parentNode) toast.remove();
  }, 20000);
}

/* ===== 初期化 ===== */
document.addEventListener("DOMContentLoaded", () => {
  startCountdown();
  scheduleAutoRefresh();

  // テーブル行のカーソル
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });

  // 初回タイムスタンプを取得
  fetch("/api/updates")
    .then(r => r.json())
    .then(updates => {
      if (updates.length) _lastKnownTimestamp = updates[0].timestamp;
    })
    .catch(() => {});
});
