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

    const show =
      (activeFilters.status     === "all" || status     === activeFilters.status) &&
      (activeFilters.difficulty === "all" || difficulty === activeFilters.difficulty) &&
      (!activeFilters.hotOnly || hot) &&
      (!activeFilters.search  || name.includes(activeFilters.search.toLowerCase()));

    row.classList.toggle("hidden", !show);
    if (show) visible++;
  });

  hotCards.forEach(card => {
    const show =
      (activeFilters.status     === "all" || card.dataset.status === activeFilters.status) &&
      (activeFilters.difficulty === "all" || card.dataset.difficulty === activeFilters.difficulty) &&
      (!activeFilters.search || (card.dataset.name || "").includes(activeFilters.search.toLowerCase()));
    card.style.display = show ? "" : "none";
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

/* ===== テーブルソート ===== */

function sortTable(col) {
  if (sortState.col === col) sortState.dir *= -1;
  else { sortState.col = col; sortState.dir = 1; }

  const tbody = document.getElementById("airdrop-tbody");
  const rows  = Array.from(tbody.querySelectorAll(".airdrop-row"));

  rows.sort((a, b) => {
    if (col === "estimated_value_usd" || col === "value") {
      return (parseFloat(a.dataset.value || "0") - parseFloat(b.dataset.value || "0")) * sortState.dir;
    }
    const ai = colIndex(col);
    const av = a.dataset[col] || a.querySelector(`td:nth-child(${ai})`)?.textContent.trim() || "";
    const bv = b.dataset[col] || b.querySelector(`td:nth-child(${ai})`)?.textContent.trim() || "";
    return av.localeCompare(bv, "ja") * sortState.dir;
  });

  rows.forEach(row => tbody.appendChild(row));
}

function colIndex(col) {
  return { name: 1, category: 2, type: 3, estimated_value_usd: 4, difficulty: 5, status: 6, end_date: 7 }[col] || 1;
}

/* ===== 更新バナー展開/折りたたみ ===== */

function toggleBannerDetail() {
  const detail = document.getElementById("banner-detail");
  const btn    = document.getElementById("banner-toggle-btn");
  if (!detail) return;

  const isOpen = detail.style.display !== "none";
  detail.style.display = isOpen ? "none" : "flex";
  btn.classList.toggle("open", !isOpen);
  btn.textContent = isOpen ? "▼" : "▲";
}

/* ===== リアルタイム更新チェック ===== */

let _lastKnownTimestamp = null;
let _lastKnownHotCount  = null;

function _initKnownState() {
  const timeEl = document.querySelector(".update-time");
  if (timeEl) _lastKnownTimestamp = timeEl.textContent.trim();

  // ページロード時のホット件数を記録
  const hotChip = document.querySelector(".stat-hot strong");
  if (hotChip) _lastKnownHotCount = parseInt(hotChip.textContent, 10) || 0;
}

async function checkForUpdates() {
  try {
    const res     = await fetch("/api/updates");
    const updates = await res.json();
    if (!updates.length) return;

    const latest = updates[0];

    // タイムスタンプが変化していたらリロード通知
    if (_lastKnownTimestamp && latest.time_jst !== _lastKnownTimestamp) {
      showRefreshNotice();
      _lastKnownTimestamp = latest.time_jst;
    }

    // ホット件数が増加していたら緊急通知
    const newHotCount = latest.hot_count || 0;
    if (_lastKnownHotCount !== null && newHotCount > _lastKnownHotCount) {
      showHotCountAlert(newHotCount - _lastKnownHotCount);
    }
    _lastKnownHotCount = newHotCount;

  } catch (_) { /* ネットワークエラーは無視 */ }
}

function showRefreshNotice() {
  // 既存の通知があれば再表示しない
  if (document.getElementById("refresh-notice")) return;

  const notice = document.createElement("div");
  notice.id = "refresh-notice";
  notice.style.cssText = [
    "position:fixed;bottom:24px;right:24px;",
    "background:#7c4dff;color:white;",
    "padding:14px 20px;border-radius:12px;",
    "font-size:14px;font-weight:700;cursor:pointer;",
    "z-index:9999;box-shadow:0 4px 24px rgba(0,0,0,0.5);",
    "animation:slideInRight 0.3s ease;",
    "max-width:280px;line-height:1.4;",
  ].join("");
  notice.textContent = "🔄 新しい更新があります — クリックで再読み込み";
  notice.onclick = () => location.reload();
  document.body.appendChild(notice);
  setTimeout(() => notice.remove(), 20000);
}

function showHotCountAlert(newCount) {
  if (document.getElementById("hot-count-alert")) return;

  const alert = document.createElement("div");
  alert.id = "hot-count-alert";
  alert.style.cssText = [
    "position:fixed;bottom:24px;left:24px;",
    "background:linear-gradient(135deg,#dc3545,#ff4757);color:white;",
    "padding:14px 20px;border-radius:12px;",
    "font-size:14px;font-weight:800;cursor:pointer;",
    "z-index:9999;box-shadow:0 4px 24px rgba(220,53,69,0.5);",
    "animation:slideInLeft 0.3s ease;",
    "max-width:300px;line-height:1.4;",
  ].join("");
  alert.innerHTML = `🚨 ホット案件が<strong>+${newCount}件</strong>追加されました！<br><span style="font-size:12px;font-weight:400;opacity:0.9;">クリックで再読み込み</span>`;
  alert.onclick = () => location.reload();
  document.body.appendChild(alert);
  setTimeout(() => alert.remove(), 25000);
}

/* ===== CSS アニメーション追加 ===== */

function injectAnimationStyles() {
  const style = document.createElement("style");
  style.textContent = `
    @keyframes slideInRight {
      from { opacity:0; transform:translateX(80px); }
      to   { opacity:1; transform:translateX(0); }
    }
    @keyframes slideInLeft {
      from { opacity:0; transform:translateX(-80px); }
      to   { opacity:1; transform:translateX(0); }
    }
  `;
  document.head.appendChild(style);
}

/* ===== ポーリングスケジューラ ===== */

function startPolling() {
  // 5分ごとにホット案件変化をチェック (更新頻度とのバランス)
  const INTERVAL_MS = 5 * 60 * 1000;
  const poll = () => {
    checkForUpdates().finally(() => setTimeout(poll, INTERVAL_MS));
  };
  setTimeout(poll, INTERVAL_MS);
}

/* ===== 初期化 ===== */

document.addEventListener("DOMContentLoaded", () => {
  injectAnimationStyles();
  _initKnownState();
  startPolling();

  // テーブル行: ツールチップカーソル
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "help";
  });

  // hot-flash: 10秒後に自動フェードアウト
  const flash = document.getElementById("hot-flash");
  if (flash) {
    setTimeout(() => {
      flash.style.transition = "opacity 0.5s";
      flash.style.opacity = "0";
      setTimeout(() => flash.remove(), 500);
    }, 10000);
  }
});
