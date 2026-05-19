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

// ===== 次回更新カウントダウン =====
function updateCountdown() {
  const el = document.getElementById("next-update-countdown");
  if (!el) return;

  const now = new Date();
  // 毎日 08:00 JST (UTC+9)
  const jstOffset = 9 * 60;
  const nowJST = new Date(now.getTime() + (jstOffset - now.getTimezoneOffset()) * 60000);
  const next = new Date(nowJST);
  next.setHours(8, 0, 0, 0);
  if (nowJST.getHours() >= 8) next.setDate(next.getDate() + 1);

  const diff = next - nowJST;
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);

  el.textContent = `次回更新まで ${h}時間${m}分${s}秒`;
}

// ===== 自動リロード: 5分ごとにチェック =====
let lastKnownTimestamp = null;

function checkForUpdates() {
  fetch("/api/updates")
    .then(r => r.json())
    .then(updates => {
      if (!updates || updates.length === 0) return;
      const ts = updates[0].timestamp;
      if (lastKnownTimestamp === null) {
        lastKnownTimestamp = ts;
        return;
      }
      if (ts !== lastKnownTimestamp) {
        showRefreshToast();
        lastKnownTimestamp = ts;
      }
    })
    .catch(() => {});
}

function showRefreshToast() {
  // 既存トーストを除去
  document.querySelectorAll(".refresh-toast").forEach(el => el.remove());

  const toast = document.createElement("div");
  toast.className = "refresh-toast";
  toast.innerHTML = "🔄 新しい更新があります<br><small>クリックで再読み込み</small>";
  toast.onclick = () => location.reload();
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 20000);
}

document.addEventListener("DOMContentLoaded", () => {
  // カウントダウン更新 (1秒ごと)
  updateCountdown();
  setInterval(updateCountdown, 1000);

  // 更新チェック (5分ごと)
  checkForUpdates();
  setInterval(checkForUpdates, 5 * 60 * 1000);

  // テーブル行ツールチップ
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });
});
