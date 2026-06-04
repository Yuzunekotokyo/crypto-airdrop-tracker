/* Crypto Airdrop Tracker — フロントエンドロジック */

let activeFilters = { status: "all", difficulty: "all", hotOnly: false, search: "" };
let sortState = { col: null, dir: 1 };

/* ===== フィルター ===== */

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
    const statusOk   = activeFilters.status === "all" || status === activeFilters.status;
    const diffOk     = activeFilters.difficulty === "all" || difficulty === activeFilters.difficulty;
    const searchOk   = !activeFilters.search || name.includes(activeFilters.search.toLowerCase());
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

/* ===== 更新バナー 詳細パネル ===== */

function toggleBannerDetail() {
  const panel = document.getElementById("banner-detail");
  const btn   = document.getElementById("banner-toggle-btn");
  if (!panel) return;

  const isHidden = panel.classList.contains("hidden");
  panel.classList.toggle("hidden", !isHidden);
  if (btn) {
    btn.classList.toggle("open", isHidden);
    btn.textContent = isHidden ? "▲ 閉じる" : "▼ 詳細";
  }
}

/* ===== 次回更新カウントダウン ===== */

function updateCountdown() {
  const el = document.getElementById("next-update-countdown");
  if (!el) return;

  const now = new Date();
  const jstOffset = 9 * 60; // JST = UTC+9
  const utcMinutes = now.getUTCHours() * 60 + now.getUTCMinutes();
  const jstMinutes = (utcMinutes + jstOffset) % (24 * 60);
  const targetMinutes = 8 * 60; // 08:00 JST

  let diffMinutes = targetMinutes - jstMinutes;
  if (diffMinutes <= 0) diffMinutes += 24 * 60;

  const h = Math.floor(diffMinutes / 60);
  const m = diffMinutes % 60;
  const s = 59 - now.getSeconds(); // approximate
  el.textContent = `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
}

/* ===== 自動リフレッシュ (30分ごとにチェック) ===== */

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
          _lastKnownTimestamp = latest;
          showRefreshNotice();
        }
      })
      .catch(() => {})
      .finally(() => scheduleAutoRefresh());
  }, 30 * 60 * 1000);
}

function showRefreshNotice() {
  const existing = document.getElementById("refresh-notice");
  if (existing) existing.remove();

  const notice = document.createElement("div");
  notice.id = "refresh-notice";
  notice.style.cssText = [
    "position:fixed", "bottom:24px", "right:24px",
    "background:linear-gradient(135deg,#7c4dff,#651fff)",
    "color:white", "padding:14px 20px", "border-radius:12px",
    "font-size:14px", "font-weight:700", "cursor:pointer",
    "z-index:9999", "box-shadow:0 6px 24px rgba(0,0,0,0.5)",
    "display:flex", "align-items:center", "gap:10px",
    "animation:slideUp 0.3s ease",
  ].join(";");

  const style = document.createElement("style");
  style.textContent = "@keyframes slideUp{from{transform:translateY(60px);opacity:0}to{transform:translateY(0);opacity:1}}";
  document.head.appendChild(style);

  notice.innerHTML = `
    <span>🔄 新しい更新データがあります</span>
    <button onclick="location.reload()"
      style="background:white;color:#7c4dff;border:none;padding:5px 14px;border-radius:8px;font-weight:800;cursor:pointer;">
      再読み込み
    </button>
    <button onclick="document.getElementById('refresh-notice').remove()"
      style="background:none;border:none;color:rgba(255,255,255,0.7);font-size:18px;cursor:pointer;padding:0 4px;">
      ✕
    </button>`;
  document.body.appendChild(notice);

  setTimeout(() => { if (notice.parentNode) notice.remove(); }, 20000);
}

/* ===== 初期化 ===== */

document.addEventListener("DOMContentLoaded", () => {
  scheduleAutoRefresh();
  updateCountdown();
  setInterval(updateCountdown, 1000);

  // テーブル行にカーソルヒント
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });
});
