"""
毎日の更新処理コア。
- エアドロップデータを最新化
- 更新ログを記録
- Gmail通知を毎日送信
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
                status_label = {"active": "アクティブ", "upcoming": "近日開始", "ended": "終了"}
                old_s = status_label.get(old_a.get("status", ""), old_a.get("status", ""))
                new_s = status_label.get(new_a.get("status", ""), new_a.get("status", ""))
                diffs.append(f"ステータス: {old_s} → {new_s}")
            if old_a.get("estimated_value_usd") != new_a.get("estimated_value_usd"):
                old_v = old_a.get("estimated_value_usd", 0) or 0
                new_v = new_a.get("estimated_value_usd", 0) or 0
                diffs.append(f"推定価値: ${old_v:,} → ${new_v:,}")
            if old_a.get("is_hot") != new_a.get("is_hot"):
                diffs.append("🔥 ホット案件に昇格" if new_a.get("is_hot") else "ホット解除")
            if old_a.get("end_date") != new_a.get("end_date"):
                diffs.append(f"期限: {old_a.get('end_date','未定')} → {new_a.get('end_date','未定')}")
            if diffs:
                changed.append({
                    "name": new_a["name"],
                    "symbol": new_a.get("symbol", ""),
                    "changes": diffs,
                    "is_hot": new_a.get("is_hot", False),
                    "estimated_value_usd": new_a.get("estimated_value_usd", 0),
                    "url": new_a.get("url", ""),
                })

    return {"added": added, "removed": removed, "changed": changed}


def run_daily_update(force_email: bool = False) -> dict:
    """メイン更新処理。戻り値: 更新サマリーdict"""
    now = datetime.now(timezone.utc)
    logger.info(f"=== 日次更新開始 {now.isoformat()} ===")

    old_airdrops = _load_json(AIRDROPS_FILE, [])

    # データ取得
    new_airdrops, scraped_new = fetch_all_airdrops()
    trending = get_trending_coins()

    # 変更検出
    diff = _detect_changes(old_airdrops, new_airdrops)

    # 新規ホット案件の即時アラート (通常メールとは別に送信)
    newly_hot = [a for a in diff["added"] if a.get("is_hot")]
    for airdrop in newly_hot:
        logger.info(f"ホットアラート送信: {airdrop['name']}")
        send_hot_alert(airdrop)

    # データ保存
    _save_json(AIRDROPS_FILE, new_airdrops)

    # 更新ログ
    # JST時刻 (UTC+9)
    from datetime import timedelta
    jst_now = now + timedelta(hours=9)
    summary = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time_jst": jst_now.strftime("%Y年%m月%d日 %H:%M JST"),
        "total_airdrops": len(new_airdrops),
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "changed_count": len(diff["changed"]),
        "hot_count": sum(1 for a in new_airdrops if a.get("is_hot")),
        "added_names": [a["name"] for a in diff["added"]],
        "added_hot_names": [a["name"] for a in diff["added"] if a.get("is_hot")],
        "removed_names": diff["removed"],
        "changes": diff["changed"],
        "trending_coins": [t["name"] for t in trending[:5]],
        "email_sent": False,
    }

    updates_log = _load_json(UPDATES_FILE, [])
    updates_log.insert(0, summary)
    updates_log = updates_log[:30]  # 直近30件を保持
    _save_json(UPDATES_FILE, updates_log)

    # メール送信 — 毎日必ず送信 (force_emailまたは定期実行)
    sent = send_daily_report(new_airdrops, diff["added"], diff["changed"], trending)
    summary["email_sent"] = sent
    updates_log[0]["email_sent"] = sent
    _save_json(UPDATES_FILE, updates_log)

    logger.info(f"=== 日次更新完了: 追加{len(diff['added'])}件, 変更{len(diff['changed'])}件, メール送信{'成功' if sent else '失敗/スキップ'} ===")
    return summary
