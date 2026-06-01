/* Crypto Airdrop Tracker — フロントエンドロジック */

let activeFilters = { status: "all", difficulty: "all", hotOnly: false, search: "" };
let sortState = { col: null, dir: 1 };
let detailOpen = false;

/* ===== 更新詳細パネル ===== */
function toggleUpdateDetail() {
  const panel = document.getElementById("update-detail-panel");
  const btn   = document.getElementById("banner-toggle-btn");
  if (!panel || !btn) return;

  detailOpen = !detailOpen;
  panel.style.display = detailOpen ? "block" : "none";
  btn.textContent = detailOpen ? "閉じる ▲" : "詳細を見る ▼";
  btn.classList.toggle("open", detailOpen);
}

/* ===== フィルター ===== */
function applyFilters() {
  const rows     = document.querySelectorAll("#airdrop-tbody .airdrop-row");
  const hotCards = document.querySelectorAll(".hot-card");
  let visible = 0;

  rows.forEach(row => {
    const status = row.dataset.status;
    const difficulty = row.dataset.difficulty;
    const hot  = row.dataset.hot === "true";
    const name = row.dataset.name || "";

    const ok =
      (activeFilters.status     === "all" || status     === activeFilters.status)     &&
      (activeFilters.difficulty === "all" || difficulty === activeFilters.difficulty) &&
      (!activeFilters.hotOnly   || hot)                                               &&
      (!activeFilters.search    || name.includes(activeFilters.search));

    row.classList.toggle("hidden", !ok);
    if (ok) visible++;
  });

  hotCards.forEach(card => {
    const ok =
      (activeFilters.status     === "all" || card.dataset.status     === activeFilters.status)     &&
      (activeFilters.difficulty === "all" || card.dataset.difficulty === activeFilters.difficulty) &&
      (!activeFilters.search    || (card.dataset.name || "").includes(activeFilters.search));
    card.style.display = ok ? "" : "none";
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
  sortState.dir = sortState.col === col ? sortState.dir * -1 : 1;
  sortState.col = col;

  const tbody = document.getElementById("airdrop-tbody");
  const rows  = Array.from(tbody.querySelectorAll(".airdrop-row"));

  rows.sort((a, b) => {
    if (col === "estimated_value_usd") {
      return (parseFloat(a.dataset.value || "0") - parseFloat(b.dataset.value || "0")) * sortState.dir;
    }
    const idx = { name:1, category:2, type:3, estimated_value_usd:4, difficulty:5, status:6, end_date:7 }[col] || 1;
    const av = a.querySelector(`td:nth-child(${idx})`).textContent.trim();
    const bv = b.querySelector(`td:nth-child(${idx})`).textContent.trim();
    return av.localeCompare(bv, "ja") * sortState.dir;
  });

  rows.forEach(r => tbody.appendChild(r));
}

/* ===== Toast通知 ===== */
function showToast(message, isHot = false, duration = 12000) {
  const el = document.createElement("div");
  el.className = "toast-notification" + (isHot ? " toast-hot" : "");
  el.innerHTML = `<span>${message}</span><small style="opacity:0.6;font-size:11px;white-space:nowrap;">クリックで閉じる</small>`;
  el.onclick = () => el.remove();
  document.body.appendChild(el);
  setTimeout(() => el && el.parentNode && el.remove(), duration);
}

/* ===== 自動リフレッシュ ===== */
let lastKnownTimestamp = null;

function scheduleAutoRefresh() {
  setTimeout(async () => {
    try {
      const updates = await fetch("/api/updates").then(r => r.json());
      if (updates.length > 0) {
        const latest = updates[0];
        if (lastKnownTimestamp && latest.timestamp !== lastKnownTimestamp) {
          const hasHot  = latest.hot_count > 0;
          const hasNew  = latest.added_count > 0;
          const msg = hasNew
            ? `🆕 新着${latest.added_count}件のエアドロップが追加されました。再読み込みで確認できます`
            : `🔄 最新情報に更新されました (${latest.time_jst})`;
          showToast(msg, hasHot);
          setTimeout(() => location.reload(), 8000);
        }
        lastKnownTimestamp = latest.timestamp;
      }
    } catch (_) {}
    scheduleAutoRefresh();
  }, 30 * 60 * 1000);
}

/* ===== 初期化 ===== */
document.addEventListener("DOMContentLoaded", () => {
  // 最初のタイムスタンプを記録
  fetch("/api/updates")
    .then(r => r.json())
    .then(updates => {
      if (updates.length > 0) lastKnownTimestamp = updates[0].timestamp;
    })
    .catch(() => {});

  scheduleAutoRefresh();

  // テーブル行カーソル
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });
});
