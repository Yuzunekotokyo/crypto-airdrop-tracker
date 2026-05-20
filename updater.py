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

JST = timezone(timedelta(hours=9))


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
                old_val = old_a.get("estimated_value_usd", 0) or 0
                new_val = new_a.get("estimated_value_usd", 0) or 0
                direction = "⬆️" if new_val > old_val else "⬇️"
                diffs.append(
                    f"推定価値 {direction}: ${old_val:,} → ${new_val:,}"
                )
            if old_a.get("is_hot") != new_a.get("is_hot"):
                diffs.append(
                    "🔥 ホット昇格" if new_a.get("is_hot") else "ホット解除"
                )
            if diffs:
                changed.append({"name": new_a["name"], "changes": diffs})

    return {"added": added, "removed": removed, "changed": changed}


def run_daily_update(force_email: bool = False) -> dict:
    """メイン更新処理。戻り値: 更新サマリーdict"""
    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc.astimezone(JST)
    logger.info(f"=== 日次更新開始 {now_utc.isoformat()} ===")

    old_airdrops = _load_json(AIRDROPS_FILE, [])

    # データ取得
    new_airdrops, scraped_new = fetch_all_airdrops()
    trending = get_trending_coins()

    # 変更検出
    diff = _detect_changes(old_airdrops, new_airdrops)

    # 新規ホット案件 (新着かつ is_hot=True のもの)
    newly_hot = [a for a in diff["added"] if a.get("is_hot")]
    # 既存からホット昇格したもの
    hot_upgraded = [c for c in diff["changed"] if any("ホット昇格" in d for d in c["changes"])]

    # ホット案件即時アラート
    for airdrop in newly_hot:
        send_hot_alert(airdrop)

    # データ保存
    _save_json(AIRDROPS_FILE, new_airdrops)

    # 更新ログ
    summary = {
        "timestamp": now_utc.isoformat(),
        "date": now_jst.strftime("%Y-%m-%d"),
        "time_jst": now_jst.strftime("%Y年%m月%d日 %H:%M"),
        "total_airdrops": len(new_airdrops),
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "changed_count": len(diff["changed"]),
        "hot_count": sum(1 for a in new_airdrops if a.get("is_hot")),
        "added_names": [a["name"] for a in diff["added"]],
        "removed_names": diff["removed"],
        "changes": diff["changed"],
        "newly_hot_names": [a["name"] for a in newly_hot],
        "hot_upgraded_names": [c["name"] for c in hot_upgraded],
        # 新着の中で推定価値が高い順トップ3
        "top_new": sorted(
            [{"name": a["name"], "value": a.get("estimated_value_usd", 0)}
             for a in diff["added"] if a.get("estimated_value_usd", 0) > 0],
            key=lambda x: -x["value"]
        )[:3],
        "trending_coins": [t["name"] for t in trending[:5]],
        "email_sent": False,
    }

    updates_log = _load_json(UPDATES_FILE, [])
    updates_log.insert(0, summary)
    updates_log = updates_log[:30]  # 直近30件を保持
    _save_json(UPDATES_FILE, updates_log)

    # メール送信: 新着あり・ホット案件変化・強制送信 のいずれか
    should_email = force_email or diff["added"] or newly_hot or hot_upgraded
    if should_email:
        sent = send_daily_report(new_airdrops, diff, trending, summary)
        summary["email_sent"] = sent
        updates_log[0]["email_sent"] = sent
        _save_json(UPDATES_FILE, updates_log)

    logger.info(
        f"=== 日次更新完了: 追加{len(diff['added'])}件, "
        f"変更{len(diff['changed'])}件, ホット新着{len(newly_hot)}件 ==="
    )
    return summary
