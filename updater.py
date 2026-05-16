"""
毎日の更新処理コア。
- エアドロップデータを最新化
- 更新ログを記録
- Gmail通知を送信 (毎日送信 + HOT案件出現時は即時アラート)
"""

import json
import logging
import os
from datetime import datetime, timezone

from config import AIRDROPS_FILE, UPDATES_FILE, DATA_DIR
from fetchers.airdrop_fetcher import fetch_all_airdrops
from fetchers.coingecko import get_trending_coins
from notifier.gmail import send_daily_report, send_hot_alert

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
                old_val = old_a.get("estimated_value_usd", 0)
                new_val = new_a.get("estimated_value_usd", 0)
                diffs.append(f"推定価値: ${old_val:,} → ${new_val:,}")
            if old_a.get("is_hot") != new_a.get("is_hot"):
                diffs.append("HOT案件に昇格" if new_a.get("is_hot") else "HOT案件から外れた")
            if diffs:
                changed.append({"name": new_a["name"], "changes": diffs})

    return {"added": added, "removed": removed, "changed": changed}


def run_daily_update(force_email: bool = False) -> dict:
    """メイン更新処理。毎日メールを送信する。"""
    now = datetime.now(timezone.utc)
    logger.info(f"=== 日次更新開始 {now.isoformat()} ===")

    old_airdrops = _load_json(AIRDROPS_FILE, [])

    # データ取得
    new_airdrops, scraped_new = fetch_all_airdrops()
    trending = get_trending_coins()

    # 変更検出
    diff = _detect_changes(old_airdrops, new_airdrops)

    # 新規HOT案件が追加されたら即時アラートメールを送信
    newly_hot = [a for a in diff["added"] if a.get("is_hot")]
    hot_alerts_sent = 0
    for airdrop in newly_hot:
        if send_hot_alert(airdrop):
            hot_alerts_sent += 1
            logger.info(f"HOTアラート送信: {airdrop['name']}")

    # データ保存
    _save_json(AIRDROPS_FILE, new_airdrops)

    # 更新ログ
    summary = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time_jst": (now.astimezone()).strftime("%Y年%m月%d日 %H:%M"),
        "total_airdrops": len(new_airdrops),
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "changed_count": len(diff["changed"]),
        "hot_count": sum(1 for a in new_airdrops if a.get("is_hot")),
        "added_names": [a["name"] for a in diff["added"]],
        "removed_names": diff["removed"],
        "changes": diff["changed"],
        "trending_coins": [t["name"] for t in trending[:5]],
        "newly_hot_names": [a["name"] for a in newly_hot],
        "email_sent": False,
        "hot_alerts_sent": hot_alerts_sent,
    }

    updates_log = _load_json(UPDATES_FILE, [])
    updates_log.insert(0, summary)
    updates_log = updates_log[:30]  # 直近30件保持
    _save_json(UPDATES_FILE, updates_log)

    # 毎日デイリーレポートを送信 (force_email, 新着あり, HOT変化のいずれかで送信)
    should_email = force_email or True  # 毎日必ず送信
    if should_email:
        sent = send_daily_report(new_airdrops, scraped_new, diff, trending)
        summary["email_sent"] = sent
        updates_log[0]["email_sent"] = sent
        _save_json(UPDATES_FILE, updates_log)

    logger.info(
        f"=== 日次更新完了: 追加{len(diff['added'])}件, 変更{len(diff['changed'])}件, "
        f"HOTアラート{hot_alerts_sent}件, メール{'送信済' if summary['email_sent'] else 'スキップ'} ==="
    )
    return summary
