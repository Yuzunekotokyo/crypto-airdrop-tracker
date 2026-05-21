"""
毎日の更新処理コア。
- エアドロップデータを最新化
- 市場データ・エアドロップ候補を取得・保存
- 更新ログを記録
- Gmail通知を送信
"""

import json
import logging
import os
from datetime import datetime, timezone

from config import AIRDROPS_FILE, UPDATES_FILE, NEWS_FILE, DATA_DIR
from fetchers.airdrop_fetcher import fetch_all_airdrops
from fetchers.coingecko import get_trending_coins
from fetchers.news_fetcher import (
    fetch_major_prices,
    fetch_global_market,
    fetch_airdrop_candidates,
    fetch_top_chains,
)
from notifier.gmail import send_daily_report, send_hot_alert, send_new_candidate_alert

logger = logging.getLogger(__name__)


def _load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def _save_json(path: str, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _detect_changes(old_airdrops: list[dict], new_airdrops: list[dict]) -> dict:
    old_ids = {a["id"]: a for a in old_airdrops}
    new_ids = {a["id"]: a for a in new_airdrops}

    added = [a for aid, a in new_ids.items() if aid not in old_ids]
    removed = [a["name"] for aid, a in old_ids.items() if aid not in new_ids]
    changed = []
    for aid, new_a in new_ids.items():
        if aid in old_ids:
            old_a = old_ids[aid]
            diffs = []
            if old_a.get("status") != new_a.get("status"):
                diffs.append(f"ステータス: {old_a.get('status')} → {new_a.get('status')}")
            if old_a.get("estimated_value_usd") != new_a.get("estimated_value_usd"):
                diffs.append(
                    f"推定価値: ${old_a.get('estimated_value_usd',0):,} → ${new_a.get('estimated_value_usd',0):,}"
                )
            if diffs:
                changed.append({"name": new_a["name"], "changes": diffs})

    return {"added": added, "removed": removed, "changed": changed}


def _detect_new_candidates(old_candidates: list[dict], new_candidates: list[dict]) -> list[dict]:
    """DeFiLlamaで前回から新たに現れたエアドロップ候補を検出"""
    old_names = {c["name"].lower() for c in old_candidates}
    return [c for c in new_candidates if c["name"].lower() not in old_names]


def run_daily_update(force_email: bool = False) -> dict:
    """メイン更新処理。戻り値: 更新サマリーdict"""
    now = datetime.now(timezone.utc)
    logger.info(f"=== 日次更新開始 {now.isoformat()} ===")

    old_airdrops = _load_json(AIRDROPS_FILE, [])
    old_news = _load_json(NEWS_FILE, {})
    old_candidates = old_news.get("airdrop_candidates", [])

    # --- エアドロップデータ取得 ---
    new_airdrops, scraped_new = fetch_all_airdrops()
    trending = get_trending_coins()

    # --- 市場データ取得 ---
    prices = fetch_major_prices()
    global_market = fetch_global_market()
    airdrop_candidates = fetch_airdrop_candidates()
    top_chains = fetch_top_chains()

    # --- 変更検出 ---
    diff = _detect_changes(old_airdrops, new_airdrops)
    new_candidates = _detect_new_candidates(old_candidates, airdrop_candidates)

    # --- 新規ホット案件アラート (即時メール) ---
    newly_hot = [a for a in diff["added"] if a.get("is_hot")]
    for airdrop in newly_hot:
        send_hot_alert(airdrop)

    # --- 新候補出現アラート (即時メール) ---
    if new_candidates:
        send_new_candidate_alert(new_candidates)

    # --- データ保存 ---
    _save_json(AIRDROPS_FILE, new_airdrops)

    news_data = {
        "updated_at": now.isoformat(),
        "updated_jst": now.astimezone().strftime("%Y年%m月%d日 %H:%M"),
        "prices": prices,
        "global_market": global_market,
        "airdrop_candidates": airdrop_candidates,
        "top_chains": top_chains,
        "trending": trending[:5],
        "new_candidates": new_candidates,
    }
    _save_json(NEWS_FILE, news_data)

    # --- 更新ログ ---
    summary = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time_jst": now.astimezone().strftime("%Y年%m月%d日 %H:%M"),
        "total_airdrops": len(new_airdrops),
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "changed_count": len(diff["changed"]),
        "hot_count": sum(1 for a in new_airdrops if a.get("is_hot")),
        "added_names": [a["name"] for a in diff["added"]],
        "removed_names": diff["removed"],
        "changes": diff["changed"],
        "trending_coins": [t["name"] for t in trending[:5]],
        "new_candidates_count": len(new_candidates),
        "new_candidate_names": [c["name"] for c in new_candidates],
        "btc_price_usd": prices.get("BTC", {}).get("usd", 0),
        "market_change_24h": global_market.get("market_cap_change_24h", 0),
        "email_sent": False,
    }

    updates_log = _load_json(UPDATES_FILE, [])
    updates_log.insert(0, summary)
    updates_log = updates_log[:30]
    _save_json(UPDATES_FILE, updates_log)

    # --- メール送信 ---
    # 条件: 新着あり / 新規ホット案件 / 高TVL新候補出現 / 強制送信
    should_email = force_email or diff["added"] or newly_hot or new_candidates
    if should_email:
        sent = send_daily_report(new_airdrops, scraped_new, trending, news_data)
        summary["email_sent"] = sent
        updates_log[0]["email_sent"] = sent
        _save_json(UPDATES_FILE, updates_log)

    logger.info(
        f"=== 日次更新完了: 追加{len(diff['added'])}件, 変更{len(diff['changed'])}件, "
        f"新候補{len(new_candidates)}件 ==="
    )
    return summary
