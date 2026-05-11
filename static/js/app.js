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

/* ===== 次回更新カウントダウン (毎日 08:00 JST) ===== */
function updateCountdown() {
  const el = document.getElementById("next-update-countdown");
  if (!el) return;

  const now = new Date();
  // JST = UTC+9
  const jstNow = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  const target = new Date(jstNow);
  target.setUTCHours(8 - 9, 0, 0, 0); // 08:00 JST = 23:00 UTC前日
  // JSTで08:00を設定
  target.setUTCHours(target.getUTCHours()); // 正規化
  // もし今日の08:00 JSTをすでに過ぎていたら翌日の08:00 JSTを設定
  const jstHour = jstNow.getUTCHours();
  const jstMin  = jstNow.getUTCMinutes();
  let minutesUntil = (8 * 60) - (jstHour * 60 + jstMin);
  if (minutesUntil <= 0) minutesUntil += 24 * 60;

  const h = Math.floor(minutesUntil / 60);
  const m = minutesUntil % 60;

  if (h === 0) {
    el.textContent = `⏱ あと${m}分で更新`;
    el.style.color = "#ff6348";
  } else {
    el.textContent = `⏱ 次回更新まで ${h}時間${m}分`;
  }
}

/* ===== 自動リロード: 10分ごとにチェック ===== */
function scheduleAutoRefresh() {
  setTimeout(() => {
    fetch("/api/updates")
      .then(r => r.json())
      .then(updates => {
        if (updates.length > 0) {
          const pageTimeEl = document.querySelector(".update-time");
          if (pageTimeEl && updates[0].time_jst && !pageTimeEl.textContent.includes(updates[0].date)) {
            showRefreshNotice();
          }
        }
      })
      .catch(() => {})
      .finally(() => scheduleAutoRefresh());
  }, 10 * 60 * 1000); // 10分ごと
}

function showRefreshNotice() {
  if (document.getElementById("refresh-notice")) return;
  const notice = document.createElement("div");
  notice.id = "refresh-notice";
  notice.style.cssText = [
    "position:fixed", "bottom:20px", "right:20px",
    "background:#7c4dff", "color:white",
    "padding:14px 20px", "border-radius:10px",
    "font-size:14px", "font-weight:700",
    "cursor:pointer", "z-index:999",
    "box-shadow:0 4px 20px rgba(0,0,0,0.4)",
    "animation:slideUp 0.3s ease-out",
  ].join(";");
  notice.textContent = "🔄 新しい更新があります — クリックで再読み込み";
  notice.onclick = () => location.reload();
  document.body.appendChild(notice);
  setTimeout(() => notice.remove(), 20000);
}

document.addEventListener("DOMContentLoaded", () => {
  // カウントダウン起動 (1分ごとに更新)
  updateCountdown();
  setInterval(updateCountdown, 60 * 1000);

  // 自動リフレッシュチェック起動
  scheduleAutoRefresh();

  // テーブル行ツールチップ
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });
});
