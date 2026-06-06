/* Crypto Airdrop Tracker — フロントエンドロジック */

let activeFilters = { status: "all", difficulty: "all", hotOnly: false, search: "" };
let sortState = { col: null, dir: 1 };

function applyFilters() {
  const rows = document.querySelectorAll("#airdrop-tbody .airdrop-row");
  const hotCards = document.querySelectorAll(".hot-card");
  let visible = 0;

  rows.forEach(row => {
    const status = row.dataset.status;
    const difficulty = row.dataset.difficulty;
    const hot = row.dataset.hot === "true";
    const name = row.dataset.name || "";

    const statusOk = activeFilters.status === "all" || status === activeFilters.status;
    const diffOk   = activeFilters.difficulty === "all" || difficulty === activeFilters.difficulty;
    const hotOk    = !activeFilters.hotOnly || hot;
    const searchOk = !activeFilters.search || name.includes(activeFilters.search.toLowerCase());

    const show = statusOk && diffOk && hotOk && searchOk;
    row.classList.toggle("hidden", !show);
    if (show) visible++;
  });

  hotCards.forEach(card => {
    const status = card.dataset.status;
    const difficulty = card.dataset.difficulty;
    const name = card.dataset.name || "";
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
    let av = a.dataset[col] || a.querySelector(`td:nth-child(${colIndex(col)})`).textContent.trim();
    let bv = b.dataset[col] || b.querySelector(`td:nth-child(${colIndex(col)})`).textContent.trim();

    if (col === "estimated_value_usd" || col === "value") {
      av = parseFloat(a.dataset.value || "0");
      bv = parseFloat(b.dataset.value || "0");
      return (av - bv) * sortState.dir;
    }

    return av.localeCompare(bv, "ja") * sortState.dir;
  });

  rows.forEach(row => tbody.appendChild(row));
}

function colIndex(col) {
  const map = { name: 1, category: 2, type: 3, estimated_value_usd: 4, difficulty: 5, status: 6, end_date: 7 };
  return map[col] || 1;
}

// 次回更新までのカウントダウン (毎日08:00 JST)
function updateCountdown() {
  const timer = document.getElementById("next-update-timer");
  if (!timer) return;

  const now = new Date();
  // JST = UTC+9
  const jstOffset = 9 * 60; // minutes
  const jstNow = new Date(now.getTime() + (jstOffset + now.getTimezoneOffset()) * 60000);

  const next = new Date(jstNow);
  next.setHours(8, 0, 0, 0);
  if (jstNow >= next) next.setDate(next.getDate() + 1);

  const diff = next - jstNow;
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);

  timer.textContent = `次回更新まで: ${h}時間${m}分${s}秒`;
}

// 自動リロード: 30分ごとに更新チェック
function scheduleAutoRefresh() {
  setTimeout(() => {
    fetch("/api/updates")
      .then(r => r.json())
      .then(updates => {
        if (updates.length > 0) {
          const timeEl = document.querySelector(".update-time");
          if (timeEl && !timeEl.textContent.includes(updates[0].date)) {
            showRefreshNotice();
          }
        }
      })
      .catch(() => {})
      .finally(() => scheduleAutoRefresh());
  }, 30 * 60 * 1000);
}

function showRefreshNotice() {
  if (document.getElementById("refresh-notice")) return;
  const notice = document.createElement("div");
  notice.id = "refresh-notice";
  notice.style.cssText = [
    "position:fixed",
    "bottom:20px",
    "right:20px",
    "background:linear-gradient(135deg,#7c4dff,#651fff)",
    "color:white",
    "padding:14px 20px",
    "border-radius:10px",
    "font-size:14px",
    "font-weight:700",
    "cursor:pointer",
    "z-index:999",
    "box-shadow:0 4px 20px rgba(0,0,0,0.4)",
    "animation:banner-slide-in 0.3s ease",
  ].join(";");
  notice.textContent = "🔄 新しい更新があります — クリックで再読み込み";
  notice.onclick = () => location.reload();
  document.body.appendChild(notice);
  setTimeout(() => notice.remove(), 15000);
}

document.addEventListener("DOMContentLoaded", () => {
  scheduleAutoRefresh();
  setInterval(updateCountdown, 1000);
  updateCountdown();

  // テーブル行: カーソルをポインターに
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });
});
