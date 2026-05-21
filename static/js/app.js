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

// 自動リロード: 毎10分チェック
const _pageLoadTime = Date.now();

function scheduleAutoRefresh() {
  setTimeout(() => {
    fetch("/api/updates")
      .then(r => r.json())
      .then(updates => {
        if (updates.length > 0) {
          const latestTs = new Date(updates[0].timestamp).getTime();
          if (latestTs > _pageLoadTime) {
            showRefreshNotice(updates[0]);
          }
        }
      })
      .catch(() => {})
      .finally(() => scheduleAutoRefresh());
  }, 10 * 60 * 1000);
}

function showRefreshNotice(update) {
  const existing = document.getElementById("refresh-notice");
  if (existing) return;

  const parts = [];
  if (update.added_count > 0) parts.push(`🆕 新着${update.added_count}件`);
  if (update.new_candidates_count > 0) parts.push(`💡 新候補${update.new_candidates_count}件`);
  const detail = parts.length ? ` (${parts.join(' ')})` : "";

  const notice = document.createElement("div");
  notice.id = "refresh-notice";
  notice.style.cssText = "position:fixed;bottom:20px;right:20px;background:linear-gradient(135deg,#7c4dff,#ff4757);color:white;padding:14px 20px;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;z-index:999;box-shadow:0 4px 20px rgba(0,0,0,0.5);max-width:340px;";
  notice.innerHTML = `🔄 新しい更新があります${detail}<br><span style="font-size:11px;opacity:0.8;font-weight:400;">${update.time_jst} — クリックで再読み込み</span>`;
  notice.onclick = () => location.reload();
  document.body.appendChild(notice);
  setTimeout(() => notice.remove(), 20000);
}

document.addEventListener("DOMContentLoaded", () => {
  scheduleAutoRefresh();

  // テーブル行にツールチップ
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });
});
