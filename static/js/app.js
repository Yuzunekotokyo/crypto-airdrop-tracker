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

/* バナーを閉じてセッション中は非表示 */
function closeBanner() {
  const banner = document.getElementById("update-banner");
  if (banner) {
    banner.style.transition = "opacity 0.3s";
    banner.style.opacity = "0";
    setTimeout(() => { banner.style.display = "none"; }, 300);
    try { sessionStorage.setItem("banner_closed", "1"); } catch(e) {}
  }
}

/* 自動リロード: 10分おきにAPIを確認し、新しい更新があればトースト表示 */
let _lastKnownTimestamp = null;

function scheduleAutoRefresh() {
  setTimeout(() => {
    fetch("/api/updates")
      .then(r => r.json())
      .then(updates => {
        if (!updates.length) return;
        const latest = updates[0];

        if (_lastKnownTimestamp === null) {
          _lastKnownTimestamp = latest.timestamp;
          return;
        }

        if (latest.timestamp !== _lastKnownTimestamp) {
          _lastKnownTimestamp = latest.timestamp;
          // 新HOT案件があれば目立つトースト
          if (latest.newly_hot_count && latest.newly_hot_count > 0) {
            showRefreshNotice(
              `🚨 新HOT案件が${latest.newly_hot_count}件登場！ページを更新してください`,
              "#dc3545"
            );
          } else {
            showRefreshNotice("🔄 新しい更新があります — クリックで再読み込み", "#7c4dff");
          }
        }
      })
      .catch(() => {})
      .finally(() => scheduleAutoRefresh());
  }, 10 * 60 * 1000); // 10分ごと
}

function showRefreshNotice(message, color) {
  // 既存トーストを削除
  document.querySelectorAll(".refresh-toast").forEach(el => el.remove());

  const notice = document.createElement("div");
  notice.className = "refresh-toast";
  notice.style.cssText = `
    position: fixed; bottom: 24px; right: 24px;
    background: ${color}; color: white;
    padding: 14px 20px; border-radius: 12px;
    font-size: 14px; font-weight: 700;
    cursor: pointer; z-index: 9999;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5);
    max-width: 360px; line-height: 1.4;
    animation: toast-in 0.3s ease-out;
  `;
  notice.innerHTML = message;
  notice.onclick = () => location.reload();
  document.body.appendChild(notice);

  // 30秒後に自動消去
  setTimeout(() => {
    notice.style.transition = "opacity 0.4s";
    notice.style.opacity = "0";
    setTimeout(() => notice.remove(), 400);
  }, 30000);
}

document.addEventListener("DOMContentLoaded", () => {
  // セッション中に閉じていたらバナーを非表示
  try {
    if (sessionStorage.getItem("banner_closed") === "1") {
      const banner = document.getElementById("update-banner");
      if (banner) banner.style.display = "none";
    }
  } catch(e) {}

  // 現在のタイムスタンプを記録してから監視開始
  fetch("/api/updates")
    .then(r => r.json())
    .then(updates => {
      if (updates.length) _lastKnownTimestamp = updates[0].timestamp;
    })
    .catch(() => {})
    .finally(() => scheduleAutoRefresh());

  // テーブル行ホバーでツールチップ
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });
});
