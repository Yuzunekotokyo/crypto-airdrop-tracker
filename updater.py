"""
毎日の更新処理コア。
- エアドロップデータを最新化
- 更新ログを記録
- Gmail通知を送信
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta

from config import AIRDROPS_FILE, UPDATES_FILE, DATA_DIR
from fetchers.airdrop_fetcher import fetch_all_airdrops
from fetchers.coingecko import get_trending_coins
from notifier.gmail import send_daily_report, send_hot_alert

logger = logging.getLogger(__name__)

# 注目案件と判断する推定価値の閾値 (USD)
HOT_VALUE_THRESHOLD = 300


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
            if old_a.get("is_hot") != new_a.get("is_hot") and new_a.get("is_hot"):
                diffs.append("🔥 HOT案件に昇格")
            if diffs:
                changed.append({"name": new_a["name"], "changes": diffs})

    return {"added": added, "removed": removed, "changed": changed}


def _is_significant_update(diff: dict, newly_hot: list) -> bool:
    """注目度が高い更新かどうか判定 (即時アラートの基準)"""
    # 高額な新着案件
    high_value_new = [
        a for a in diff["added"]
        if a.get("estimated_value_usd", 0) >= HOT_VALUE_THRESHOLD
    ]
    return bool(newly_hot or high_value_new)


def run_daily_update(force_email: bool = False) -> dict:
    """メイン更新処理。戻り値: 更新サマリーdict"""
    now = datetime.now(timezone.utc)
    jst = now + timedelta(hours=9)
    logger.info(f"=== 日次更新開始 {now.isoformat()} ===")

    old_airdrops = _load_json(AIRDROPS_FILE, [])

    # データ取得
    new_airdrops, scraped_new = fetch_all_airdrops()
    trending = get_trending_coins()

    # 変更検出
    diff = _detect_changes(old_airdrops, new_airdrops)

    # 新規ホット案件: 即時アラートを送信
    newly_hot = [a for a in diff["added"] if a.get("is_hot")]
    for airdrop in newly_hot:
        send_hot_alert(airdrop)

    # 高額新着案件 (HOTフラグなしでも価値が高い)
    high_value_added = [
        a for a in diff["added"]
        if not a.get("is_hot") and a.get("estimated_value_usd", 0) >= HOT_VALUE_THRESHOLD
    ]

    # データ保存
    _save_json(AIRDROPS_FILE, new_airdrops)

    # 次回更新時刻 (翌日同時刻)
    from config import UPDATE_HOUR, UPDATE_MINUTE
    next_update_jst = jst.replace(hour=UPDATE_HOUR, minute=UPDATE_MINUTE, second=0, microsecond=0)
    if next_update_jst <= jst:
        next_update_jst += timedelta(days=1)

    # 更新ログ
    summary = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time_jst": jst.strftime("%Y年%m月%d日 %H:%M"),
        "next_update_jst": next_update_jst.strftime("%Y年%m月%d日 %H:%M"),
        "next_update_iso": next_update_jst.isoformat(),
        "total_airdrops": len(new_airdrops),
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "changed_count": len(diff["changed"]),
        "hot_count": sum(1 for a in new_airdrops if a.get("is_hot")),
        "added_names": [a["name"] for a in diff["added"]],
        "removed_names": diff["removed"],
        "changes": diff["changed"],
        "newly_hot": [
            {
                "name": a["name"],
                "estimated_value_usd": a.get("estimated_value_usd", 0),
                "category": a.get("category", ""),
                "url": a.get("url", ""),
            }
            for a in newly_hot
        ],
        "high_value_added": [
            {
                "name": a["name"],
                "estimated_value_usd": a.get("estimated_value_usd", 0),
                "category": a.get("category", ""),
                "url": a.get("url", ""),
            }
            for a in high_value_added
        ],
        "trending_coins": [t["name"] for t in trending[:5]],
        "email_sent": False,
    }

    updates_log = _load_json(UPDATES_FILE, [])
    updates_log.insert(0, summary)
    updates_log = updates_log[:30]  # 直近30件を保持
    _save_json(UPDATES_FILE, updates_log)

    # メール送信: 毎日必ず送信 (force_email でも送信可)
    is_significant = _is_significant_update(diff, newly_hot)
    sent = send_daily_report(new_airdrops, diff, trending, is_significant=is_significant)
    summary["email_sent"] = sent
    updates_log[0]["email_sent"] = sent
    _save_json(UPDATES_FILE, updates_log)

    logger.info(
        f"=== 日次更新完了: 追加{len(diff['added'])}件, 変更{len(diff['changed'])}件, "
        f"メール送信={'済' if sent else '失敗/スキップ'} ==="
    )
    return summary
