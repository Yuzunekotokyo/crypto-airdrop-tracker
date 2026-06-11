/* Crypto Airdrop Tracker — フロントエンドロジック */

let activeFilters = { status: "all", difficulty: "all", hotOnly: false, search: "" };
let sortState = { col: null, dir: 1 };
let lastUpdateTimestamp = null;

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

// 手動更新トリガー
function triggerUpdate() {
  const btn = document.getElementById("btn-update");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳ 更新中...";
  }

  const overlay = document.getElementById("update-overlay");
  if (overlay) overlay.style.display = "flex";

  fetch("/api/trigger-update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ force_email: false }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.status === "ok") {
        showToast("✅ 更新完了！ページを再読み込みします...", "success");
        setTimeout(() => location.reload(), 1500);
      } else {
        showToast("❌ 更新に失敗しました", "error");
      }
    })
    .catch(() => {
      showToast("❌ 更新に失敗しました", "error");
    })
    .finally(() => {
      if (overlay) overlay.style.display = "none";
      if (btn) {
        btn.disabled = false;
        btn.textContent = "🔄 今すぐ更新";
      }
    });
}

// トースト通知
function showToast(message, type = "info") {
  const existing = document.getElementById("app-toast");
  if (existing) existing.remove();

  const colorMap = {
    success: "#2ed573",
    error: "#ff4757",
    info: "#7c4dff",
    warning: "#ffa502",
  };

  const toast = document.createElement("div");
  toast.id = "app-toast";
  toast.style.cssText = [
    "position:fixed",
    "bottom:24px",
    "right:24px",
    `background:${colorMap[type] || colorMap.info}`,
    "color:white",
    "padding:14px 22px",
    "border-radius:10px",
    "font-size:14px",
    "font-weight:700",
    "cursor:pointer",
    "z-index:9999",
    "box-shadow:0 6px 24px rgba(0,0,0,0.4)",
    "max-width:340px",
    "line-height:1.4",
    "transition:opacity 0.3s",
  ].join(";");
  toast.textContent = message;
  toast.onclick = () => toast.remove();
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// 新しい更新があるかポーリング (5分ごと)
function scheduleAutoRefresh() {
  setTimeout(async () => {
    try {
      const r = await fetch("/api/updates");
      const updates = await r.json();
      if (updates.length > 0) {
        const serverTs = updates[0].timestamp;
        if (lastUpdateTimestamp && serverTs !== lastUpdateTimestamp) {
          showRefreshNotice(updates[0]);
        }
        lastUpdateTimestamp = serverTs;
      }
    } catch (_) {}
    scheduleAutoRefresh();
  }, 5 * 60 * 1000);
}

function showRefreshNotice(update) {
  const existing = document.getElementById("refresh-notice");
  if (existing) existing.remove();

  const addedInfo = update.added_count > 0
    ? ` 🆕 新着${update.added_count}件`
    : "";

  const notice = document.createElement("div");
  notice.id = "refresh-notice";
  notice.style.cssText = [
    "position:fixed",
    "bottom:24px",
    "left:50%",
    "transform:translateX(-50%)",
    "background:linear-gradient(135deg,#1a1a2e,#16213e)",
    "border:1px solid #7c4dff",
    "color:white",
    "padding:16px 24px",
    "border-radius:12px",
    "font-size:14px",
    "font-weight:700",
    "cursor:pointer",
    "z-index:9999",
    "box-shadow:0 6px 30px rgba(124,77,255,0.4)",
    "text-align:center",
    "min-width:280px",
  ].join(";");
  notice.innerHTML = `🔄 新しい更新があります${addedInfo}<br><span style="font-size:12px;opacity:0.8;font-weight:400;">クリックで再読み込み</span>`;
  notice.onclick = () => location.reload();
  document.body.appendChild(notice);
  setTimeout(() => notice.remove(), 20000);
}

document.addEventListener("DOMContentLoaded", () => {
  // 初期タイムスタンプ取得
  fetch("/api/updates")
    .then(r => r.json())
    .then(updates => {
      if (updates.length > 0) {
        lastUpdateTimestamp = updates[0].timestamp;
      }
    })
    .catch(() => {});

  scheduleAutoRefresh();

  // テーブル行: ツールチップでカーソル変更
  document.querySelectorAll(".airdrop-row[title]").forEach(row => {
    row.style.cursor = "pointer";
  });

  // 折りたたみ処理
  const panel = document.getElementById("daily-update-panel");
  const miniBar = document.getElementById("dup-mini-bar");
  if (panel && miniBar) {
    const obs = new MutationObserver(() => {
      const collapsed = panel.classList.contains("dup-collapsed");
      miniBar.style.display = collapsed ? "block" : "none";
    });
    obs.observe(panel, { attributes: true, attributeFilter: ["class"] });
  }
});
