"""
毎日の更新処理コア。
- エアドロップデータを最新化
- 更新ログを記録
- Gmail通知を送信
"""

import json
import logging
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import AIRDROPS_FILE, UPDATES_FILE, UPDATE_NOTES_FILE, DATA_DIR
from fetchers.airdrop_fetcher import fetch_all_airdrops
from fetchers.coingecko import get_trending_coins
from notifier.gmail import send_daily_report, send_hot_alert

logger = logging.getLogger(__name__)

JST = ZoneInfo("Asia/Tokyo")
STATUS_LABELS = {"active": "アクティブ", "upcoming": "近日/TGE待ち", "watch": "未確定・監視", "ended": "終了"}


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
                diffs.append(
                    "ステータス: "
                    f"{STATUS_LABELS.get(old_a.get('status'), old_a.get('status'))} → "
                    f"{STATUS_LABELS.get(new_a.get('status'), new_a.get('status'))}"
                )
            if old_a.get("end_date") != new_a.get("end_date"):
                diffs.append(f"期限: {old_a.get('end_date')} → {new_a.get('end_date')}")
            if old_a.get("deadline_note") != new_a.get("deadline_note") and new_a.get("deadline_note"):
                diffs.append(f"日程: {new_a.get('deadline_note')}")
            if bool(old_a.get("is_hot")) != bool(new_a.get("is_hot")):
                diffs.append("🔥 ホットに昇格" if new_a.get("is_hot") else "ホットから除外")
            if old_a.get("estimated_value_usd") != new_a.get("estimated_value_usd"):
                diffs.append(
                    f"推定価値: ${old_a.get('estimated_value_usd',0):,} → ${new_a.get('estimated_value_usd',0):,}"
                )
            if diffs:
                changed.append({"name": new_a["name"], "changes": diffs})

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

    # 新規ホット案件アラート
    newly_hot = [a for a in diff["added"] if a.get("is_hot")]
    for airdrop in newly_hot:
        send_hot_alert(airdrop)

    # データ保存
    _save_json(AIRDROPS_FILE, new_airdrops)

    now_jst = now.astimezone(JST)
    today = now_jst.strftime("%Y-%m-%d")
    updates_log = _load_json(UPDATES_FILE, [])

    # 手動/リサーチ由来の更新メモ (当日分のみ反映)
    notes = _load_json(UPDATE_NOTES_FILE, {})
    if notes.get("date") != today:
        notes = {}

    # 同じ日に変更なしで再実行された場合は、既存の更新ログを残す (最上部の更新内容を消さない)
    has_changes = bool(diff["added"] or diff["removed"] or diff["changed"])
    if not has_changes and not force_email and updates_log and updates_log[0].get("date") == today:
        updates_log[0]["last_checked_jst"] = now_jst.strftime("%Y年%m月%d日 %H:%M")
        _save_json(UPDATES_FILE, updates_log)
        logger.info("=== 日次更新完了: 変更なし (本日の更新ログを維持) ===")
        return updates_log[0]

    # 更新ログ
    summary = {
        "timestamp": now.isoformat(),
        "date": today,
        "time_jst": now_jst.strftime("%Y年%m月%d日 %H:%M JST"),
        "headline": notes.get("headline", ""),
        "highlights": notes.get("highlights", []),
        "deadlines": notes.get("deadlines", []),
        "total_airdrops": len(new_airdrops),
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]) + len(notes.get("removed_names", [])),
        "changed_count": len(diff["changed"]),
        "hot_count": sum(1 for a in new_airdrops if a.get("is_hot")),
        "added_names": [a["name"] for a in diff["added"]],
        "removed_names": diff["removed"] + notes.get("removed_names", []),
        "changes": diff["changed"],
        "trending_coins": [t["name"] for t in trending[:5]],
        "email_sent": False,
    }

    updates_log.insert(0, summary)
    updates_log = updates_log[:30]  # 直近30件を保持
    _save_json(UPDATES_FILE, updates_log)

    # メール送信 (新着あり、またはホット案件変化、または強制送信)
    should_email = force_email or diff["added"] or newly_hot
    if should_email:
        sent = send_daily_report(new_airdrops, scraped_new, trending)
        summary["email_sent"] = sent
        updates_log[0]["email_sent"] = sent
        _save_json(UPDATES_FILE, updates_log)

    logger.info(f"=== 日次更新完了: 追加{len(diff['added'])}件, 変更{len(diff['changed'])}件 ===")
    return summary
