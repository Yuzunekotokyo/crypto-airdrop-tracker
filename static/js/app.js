/* Crypto Airdrop Tracker — フロントエンドロジック */

let activeFilters = { status: "all", difficulty: "all", hotOnly: false, search: "" };
let sortState = { col: null, dir: 1 };

/* ===== バナー詳細トグル ===== */
function toggleBannerDetail() {
  const detail = document.getElementById("banner-detail");
  const btn = document.getElementById("banner-toggle-btn");
  if (!detail) return;
  const isOpen = detail.style.display !== "none";
  detail.style.display = isOpen ? "none" : "flex";
  btn.textContent = isOpen ? "▾ 詳細" : "▴ 閉じる";
}

/* ===== フィルター ===== */
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

/* ===== ソート ===== */
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
    if (col === "estimated_value_usd") {
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

/* ===== 自動リフレッシュ (30分間隔) ===== */
const REFRESH_INTERVAL_MS = 30 * 60 * 1000;
let nextRefreshAt = Date.now() + REFRESH_INTERVAL_MS;

function updateCountdown() {
  const el = document.getElementById("refresh-countdown");
  if (!el) return;
  const remaining = Math.max(0, nextRefreshAt - Date.now());
  const mins = Math.floor(remaining / 60000);
  const secs = Math.floor((remaining % 60000) / 1000);
  el.textContent = `次回チェック: ${mins}分${secs.toString().padStart(2, "0")}秒後`;
}

function scheduleAutoRefresh() {
  nextRefreshAt = Date.now() + REFRESH_INTERVAL_MS;
  setInterval(updateCountdown, 1000);

  setTimeout(function check() {
    fetch("/api/updates")
      .then(r => r.json())
      .then(updates => {
        if (updates.length > 0) {
          const serverTime = updates[0].time_jst;
          const bannerTime = document.querySelector(".update-time")?.textContent?.replace(" 更新", "").trim();
          if (serverTime && bannerTime && serverTime !== bannerTime) {
            showRefreshNotice(updates[0]);
          }
        }
      })
      .catch(() => {})
      .finally(() => {
        nextRefreshAt = Date.now() + REFRESH_INTERVAL_MS;
        setTimeout(check, REFRESH_INTERVAL_MS);
      });
  }, REFRESH_INTERVAL_MS);
}

function showRefreshNotice(update) {
  const existing = document.getElementById("refresh-notice");
  if (existing) existing.remove();

  const added = update?.added_count || 0;
  const hot = update?.hot_count || 0;
  let msg = "🔄 新しい更新があります";
  if (added > 0) msg += ` — 🆕新着${added}件`;
  if (hot > 0) msg += ` / 🔥ホット${hot}件`;
  msg += " — クリックで再読み込み";

  const notice = document.createElement("div");
  notice.id = "refresh-notice";
  notice.style.cssText = [
    "position:fixed", "bottom:24px", "right:24px",
    "background:linear-gradient(135deg,#7c4dff,#651fff)",
    "color:white", "padding:16px 22px", "border-radius:12px",
    "font-size:14px", "font-weight:700", "cursor:pointer",
    "z-index:9999", "box-shadow:0 6px 24px rgba(0,0,0,0.5)",
    "max-width:320px", "line-height:1.5", "animation:slideUp 0.3s ease"
  ].join(";");
  notice.textContent = msg;
  notice.onclick = () => location.reload();
  document.body.appendChild(notice);

  setTimeout(() => notice.remove(), 20000);
}

/* ===== 初期化 ===== */
document.addEventListener("DOMContentLoaded", () => {
  scheduleAutoRefresh();

  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });

  // 新着がある場合はバナー詳細を自動展開
  const banner = document.querySelector(".banner-has-new");
  if (banner) {
    const detail = document.getElementById("banner-detail");
    const btn = document.getElementById("banner-toggle-btn");
    if (detail) detail.style.display = "flex";
    if (btn) btn.textContent = "▴ 閉じる";
  }
});
